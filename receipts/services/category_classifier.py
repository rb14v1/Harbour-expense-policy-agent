"""
Hybrid Category Classifier - Combines keyword and semantic matching.

This module provides a two-stage classifier:
1. Keyword-based matching (fast, deterministic)
2. Semantic similarity matching (understands context)

The classifier combines both signals using configurable weights to classify
receipt expenses into predefined company expense categories.

Configuration:
- CLASSIFIER_KEYWORD_WEIGHT: Weight for keyword matching (default 0.6)
- CLASSIFIER_SEMANTIC_WEIGHT: Weight for semantic matching (default 0.4)
- CLASSIFIER_CONFIDENCE_THRESHOLD: Minimum confidence for auto-assignment (default 0.75)
- CLASSIFIER_AMBIGUITY_MARGIN: Margin between top 2 candidates (default 0.10)
"""

import logging
from typing import Dict, List, Optional, Tuple
from django.conf import settings

logger = logging.getLogger(__name__)

# Lazy-load semantic model only when needed
_semantic_model = None


def get_semantic_model():
    """Lazy-load and cache the semantic model."""
    global _semantic_model
    if _semantic_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            model_name = getattr(settings, 'CLASSIFIER_SEMANTIC_MODEL', 'all-MiniLM-L6-v2')
            logger.info(f"Loading semantic model: {model_name}")
            _semantic_model = SentenceTransformer(model_name)
            logger.info("Semantic model loaded successfully")
        except ImportError:
            logger.warning("sentence_transformers not installed. Semantic matching disabled.")
            _semantic_model = False  # Sentinel: tried to load but failed
        except Exception as e:
            logger.error(f"Failed to load semantic model: {e}. Falling back to keyword-only classification.")
            _semantic_model = False
    return _semantic_model if _semantic_model else None


class CategoryClassifier:
    """Hybrid keyword + semantic category classifier for expense receipts."""

    # Enhanced keyword dictionary with additional merchants and terms
    CATEGORY_KEYWORDS = {
        'Accommodation/Hotel': {
            'keywords': ['hotel', 'motel', 'resort', 'airbnb', 'lodging', 'inn', 'accommodation',
                        'holiday inn', 'marriott', 'hilton', 'hyatt', 'sheraton', 'westin',
                        'best western', 'ritz', 'radisson', 'novotel', 'accor', 'ihg'],
            'confidence_boost': 0.95
        },
        'Transport: Flights': {
            'keywords': ['airline', 'flight', 'aircraft', 'airfare', 'aviation', 'united',
                        'american', 'delta', 'southwest', 'virgin', 'lufthansa', 'british airways',
                        'qantas', 'air france', 'icelandair'],
            'confidence_boost': 0.90
        },
        'Transport: Luas/Bus/Train': {
            'keywords': ['train', 'railway', 'luas', 'bus', 'transit', 'metro', 'amtrak',
                        'greyhound', 'rail', 'transport', 'eurostar'],
            'confidence_boost': 0.85
        },
        'Transport: Taxis/Cab/Uber': {
            'keywords': ['taxi', 'uber', 'lyft', 'cab', 'ride share', 'ride-sharing', 'grab',
                        'ola', 'namma yatri', 'didi', 'gojek', 'rideshare', 'cab fare',
                        'taxi fare', 'ride hailing', 'ride hail'],
            'confidence_boost': 0.90
        },
        'Transport: Car Rental & Fuel': {
            'keywords': ['car rental', 'rental', 'hertz', 'enterprise', 'avis', 'budget',
                        'thrifty', 'alamo', 'europcar', 'fuel', 'gas station', 'petrol'],
            'confidence_boost': 0.90
        },
        'Software': {
            'keywords': ['software', 'subscription', 'saas', 'cloud', 'license', 'app store',
                        'microsoft', 'adobe', 'google', 'amazon', 'aws', 'azure', 'github',
                        'slack', 'salesforce', 'dropbox'],
            'confidence_boost': 0.85
        },
        'Food: Dinner - Max Claim: €/$/AUD 45 / INR700': {
            'keywords': ['restaurant', 'dinner', 'dinner time', 'olive garden', 'applebee',
                        'cheesecake factory', 'ruth chris', 'morton', 'texas roadhouse',
                        'red lobster', 'nobu'],
            'confidence_boost': 0.85
        },
        'Food: Breakfast or Lunch - Max Claim: €/$/AUD 15 / INR700': {
            'keywords': ['breakfast', 'lunch', 'cafe', 'coffee', 'bistro', 'pizzeria', 'bakery',
                        'starbucks', 'mcdonald', 'chipotle', 'panera', 'subway', 'taco',
                        'burger', 'pizza', 'sandwich', 'diner'],
            'confidence_boost': 0.80
        },
        'Stationery Consumables': {
            'keywords': ['stationery', 'office supplies', 'paper', 'pen', 'ink', 'supplies',
                        'staples', 'office depot', 'officeworks'],
            'confidence_boost': 0.80
        },
        'Training': {
            'keywords': ['training', 'course', 'workshop', 'seminar', 'education', 'school',
                        'university', 'college', 'certification', 'learning'],
            'confidence_boost': 0.85
        },
        'Phone Bills/Broadband': {
            'keywords': ['phone', 'mobile', 'broadband', 'internet', 'vodafone', 'telstra',
                        'telecom', 'verizon', 'at&t', 'tmobile', 'comcast', 'spectrum'],
            'confidence_boost': 0.85
        },
        'Bank Charges': {
            'keywords': ['bank', 'banking fee', 'overdraft', 'wire transfer fee', 'wells fargo',
                        'chase', 'bank of america', 'citibank'],
            'confidence_boost': 0.80
        },
        'Client Entertainment': {
            'keywords': ['entertainment', 'movie', 'cinema', 'theatre', 'theater', 'bar',
                        'lounge', 'club', 'nightclub', 'concert', 'event', 'show'],
            'confidence_boost': 0.80
        },
        'Computer Peripherals': {
            'keywords': ['mouse', 'keyboard', 'monitor', 'laptop', 'computer', 'hardware',
                        'apple', 'dell', 'lenovo', 'hp', 'device'],
            'confidence_boost': 0.80
        },
        'Travel Other incl. Parking & Tolls': {
            'keywords': ['parking', 'toll', 'petrol station', 'gas station', 'fuel', 'park'],
            'confidence_boost': 0.85
        },
        'Print & Postage': {
            'keywords': ['print', 'postage', 'shipping', 'courier', 'post office', 'fedex',
                        'ups', 'dhl'],
            'confidence_boost': 0.80
        },
        'Prepaid Flights': {
            'keywords': ['flight booking', 'airline booking', 'ticket booking', 'expedia', 'kayak'],
            'confidence_boost': 0.85
        },
        'Prepaid Accommodation': {
            'keywords': ['hotel booking', 'accommodation booking', 'airbnb booking', 'booking.com',
                        'trivago'],
            'confidence_boost': 0.85
        },
        'Prepaid Car Rental & Fuel': {
            'keywords': ['car rental booking', 'fuel prepaid'],
            'confidence_boost': 0.85
        },
    }

    # Category descriptions for semantic matching
    CATEGORY_DESCRIPTIONS = {
        'Accommodation/Hotel': 'Hotel rooms, lodging, accommodation bookings, resort stays',
        'Transport: Flights': 'Airline flights, airfares, flight tickets, air travel',
        'Transport: Luas/Bus/Train': 'Train tickets, bus fares, transit passes, metro rides, railway',
        'Transport: Taxis/Cab/Uber': 'Taxi rides, cab fares, Uber, Ola, ride-sharing services, Lyft, Grab',
        'Transport: Car Rental & Fuel': 'Car rentals, fuel, gas station, petrol, vehicle rental',
        'Software': 'Software licenses, subscriptions, SaaS, cloud services, applications',
        'Food: Dinner - Max Claim: €/$/AUD 45 / INR700': 'Dinner meals, restaurant dining, dinner services',
        'Food: Breakfast or Lunch - Max Claim: €/$/AUD 15 / INR700': 'Breakfast, lunch, cafe, coffee, quick meals',
        'Stationery Consumables': 'Office supplies, stationery, paper, pens, office materials',
        'Training': 'Training courses, workshops, seminars, educational programs, certifications',
        'Phone Bills/Broadband': 'Mobile phone bills, internet, broadband, telecom services',
        'Bank Charges': 'Banking fees, overdraft fees, wire transfer fees',
        'Client Entertainment': 'Entertainment, movies, theaters, bars, concerts, events',
        'Computer Peripherals': 'Computer hardware, peripherals, monitors, keyboards, laptops',
        'Travel Other incl. Parking & Tolls': 'Parking fees, toll charges, parking garages',
        'Print & Postage': 'Printing services, postage, shipping, courier services',
        'Prepaid Flights': 'Pre-booked flight tickets, flight advance bookings',
        'Prepaid Accommodation': 'Pre-booked hotel rooms, accommodation advance bookings',
        'Prepaid Car Rental & Fuel': 'Pre-booked car rentals, advance fuel reservations',
    }

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for matching: lowercase, strip whitespace."""
        if not text:
            return ''
        return text.lower().strip()

    @staticmethod
    def _calculate_keyword_score(extracted: dict) -> Tuple[str, float, str]:
        """
        Calculate keyword-based classification score.

        Returns:
            Tuple of (best_category, best_score, reason)
        """
        merchant_name = CategoryClassifier.normalize_text(
            extracted.get('merchant', {}).get('name', '')
        )
        line_items = extracted.get('line_items', [])
        line_items_desc = ' '.join([
            CategoryClassifier.normalize_text(item.get('description', ''))
            for item in line_items
        ])
        payment_method = CategoryClassifier.normalize_text(
            extracted.get('payment', {}).get('method', '')
        )

        best_category = None
        best_score = 0.0
        best_reason = ''

        for category, config in CategoryClassifier.CATEGORY_KEYWORDS.items():
            keywords_sorted = sorted(config['keywords'], key=len, reverse=True)

            for keyword in keywords_sorted:
                keyword_norm = CategoryClassifier.normalize_text(keyword)
                keyword_words = keyword_norm.split()
                match_found_in_merchant = False
                match_found_in_other = False

                if len(keyword_words) == 1:
                    match_found_in_merchant = keyword_words[0] in merchant_name.split()
                    match_found_in_other = keyword_words[0] in (line_items_desc + ' ' + payment_method).split()
                else:
                    match_found_in_merchant = keyword_norm in merchant_name
                    match_found_in_other = keyword_norm in (line_items_desc + ' ' + payment_method)

                if match_found_in_merchant or match_found_in_other:
                    score = config['confidence_boost']
                    if match_found_in_merchant:
                        score = min(1.0, score + 0.15)
                        match_source = 'merchant name'
                    else:
                        match_source = 'receipt details'

                    if score > best_score:
                        best_score = score
                        best_category = category
                        best_reason = f"Matched '{keyword}' in {match_source}"
                    break

        return best_category, best_score, best_reason

    @staticmethod
    def _calculate_semantic_score(extracted: dict) -> Tuple[Dict[str, float], bool]:
        """
        Calculate semantic similarity scores.

        Returns:
            Tuple of (category_scores_dict, has_semantic_model)
        """
        model = get_semantic_model()
        if not model:
            return {}, False

        try:
            # Construct receipt description from available fields
            parts = []
            if extracted.get('merchant', {}).get('name'):
                parts.append(f"Merchant: {extracted['merchant']['name']}")
            if extracted.get('line_items'):
                items_desc = ', '.join([
                    item.get('description', '')
                    for item in extracted.get('line_items', [])
                    if item.get('description')
                ])
                if items_desc:
                    parts.append(f"Items: {items_desc}")
            if extracted.get('payment', {}).get('method'):
                parts.append(f"Payment: {extracted['payment']['method']}")

            receipt_text = ' '.join(parts)
            if not receipt_text.strip():
                return {}, True

            # Embed receipt (use default numpy array, not tensor)
            receipt_embedding = model.encode(receipt_text)

            # Compare with category descriptions
            category_scores = {}
            import numpy as np

            # Convert to numpy for consistent handling across versions
            receipt_emb_np = np.array(receipt_embedding) if hasattr(receipt_embedding, '__iter__') else receipt_embedding.cpu().numpy()

            for category, description in CategoryClassifier.CATEGORY_DESCRIPTIONS.items():
                category_embedding = model.encode(description, convert_to_tensor=False)
                category_emb_np = np.array(category_embedding) if hasattr(category_embedding, '__iter__') else category_embedding

                # Compute cosine similarity using numpy
                dot_product = np.dot(receipt_emb_np, category_emb_np)
                norm_a = np.linalg.norm(receipt_emb_np)
                norm_b = np.linalg.norm(category_emb_np)
                similarity = float(dot_product / (norm_a * norm_b)) if (norm_a * norm_b) > 0 else 0.0
                category_scores[category] = similarity

            return category_scores, True

        except Exception as e:
            logger.warning(f"Semantic scoring failed: {e}. Using keyword-only classification.")
            return {}, True  # Return True to indicate model exists but failed to score

    @staticmethod
    def classify(extracted: dict) -> dict:
        """
        Classify receipt into expense category using hybrid approach.

        Args:
            extracted: OCR extracted data dict with structure:
                {
                    'merchant': {'name': str, ...},
                    'line_items': [{'description': str, ...}],
                    'payment': {'method': str, ...},
                    ...
                }

        Returns:
            Classification result dict:
            {
                'category': str,
                'confidence': float (0.0-1.0),
                'reason': str,
                'method': str ('keyword', 'semantic', 'hybrid', 'fallback'),
                'keyword_score': float,
                'semantic_score': float,
                'scores_by_category': dict (debug info)
            }
        """
        if not extracted:
            return {
                'category': 'Other',
                'confidence': 0.0,
                'reason': 'No receipt data available',
                'method': 'fallback',
                'keyword_score': 0.0,
                'semantic_score': 0.0,
                'scores_by_category': {}
            }

        # Step 1: Calculate keyword scores
        best_keyword_category, keyword_score, keyword_reason = CategoryClassifier._calculate_keyword_score(extracted)

        # Step 2: Calculate semantic scores
        semantic_scores, semantic_available = CategoryClassifier._calculate_semantic_score(extracted)

        # Step 3: Check for strong keyword match
        confidence_threshold = getattr(settings, 'CLASSIFIER_CONFIDENCE_THRESHOLD', 0.75)
        if best_keyword_category and keyword_score >= confidence_threshold:
            # Keyword match is strong enough - return immediately
            return {
                'category': best_keyword_category,
                'confidence': keyword_score,
                'reason': keyword_reason,
                'method': 'keyword',
                'keyword_score': keyword_score,
                'semantic_score': 0.0,
                'scores_by_category': {}
            }

        # Step 4: Semantic fallback
        if not semantic_available or not semantic_scores:
            # No semantic support and keyword wasn't strong enough
            if best_keyword_category:
                # Weak keyword match - return with lower confidence
                return {
                    'category': 'Other',
                    'confidence': 0.5,
                    'reason': 'Low confidence in keyword match. Requires manual review.',
                    'method': 'fallback',
                    'keyword_score': keyword_score,
                    'semantic_score': 0.0,
                    'scores_by_category': {}
                }
            else:
                return {
                    'category': 'Other',
                    'confidence': 0.0,
                    'reason': 'No reliable category match found',
                    'method': 'fallback',
                    'keyword_score': 0.0,
                    'semantic_score': 0.0,
                    'scores_by_category': {}
                }

        # Step 5: Hybrid scoring - combine keyword and semantic scores for borderline cases
        keyword_weight = getattr(settings, 'CLASSIFIER_KEYWORD_WEIGHT', 0.6)
        semantic_weight = getattr(settings, 'CLASSIFIER_SEMANTIC_WEIGHT', 0.4)

        # Adjust weights if only semantic is available
        if best_keyword_category is None:
            keyword_weight = 0.0
            semantic_weight = 1.0

        # Normalize semantic scores: boost since embedding model gives 0.1-0.5 for matches
        combined_scores = {}
        for category in CategoryClassifier.CATEGORY_KEYWORDS.keys():
            # Normalize keyword score: map [0.65, 1.0] to [0, 1]
            norm_keyword = max(0.0, (keyword_score - 0.65) / 0.35) if category == best_keyword_category else 0.0

            # Normalize semantic score: cosine similarity naturally gives 0.1-0.5 for related texts
            # Use it directly without aggressive boosting to avoid false positives like grocery->food
            raw_semantic = semantic_scores.get(category, 0.0)
            # Light scaling: x * 1.5 lets good matches (0.35+) reach 0.5+
            norm_semantic = raw_semantic * 1.5

            # Weighted combination
            total_weight = keyword_weight + semantic_weight
            if total_weight > 0:
                combined = (keyword_weight * norm_keyword + semantic_weight * norm_semantic) / total_weight
            else:
                combined = 0.0
            combined_scores[category] = combined

        # Sort by combined score
        sorted_categories = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        best_category = sorted_categories[0][0]
        best_combined_score = sorted_categories[0][1]

        # Check confidence threshold
        confidence_threshold = getattr(settings, 'CLASSIFIER_CONFIDENCE_THRESHOLD', 0.75)
        # Map combined score [0, 1] to confidence scale
        best_confidence = best_combined_score

        if best_confidence < confidence_threshold:
            # Check if second-best is too close (ambiguous)
            # Use a smaller margin for semantic-only cases since semantic scores naturally vary less
            ambiguity_margin = getattr(settings, 'CLASSIFIER_AMBIGUITY_MARGIN', 0.10)
            if best_keyword_category is None:
                # Semantic-only classification - smaller margin is appropriate
                ambiguity_margin = ambiguity_margin * 0.5

            second_best_score = sorted_categories[1][1] if len(sorted_categories) > 1 else 0.0
            score_gap = best_combined_score - second_best_score

            if score_gap < ambiguity_margin:
                return {
                    'category': 'Other',
                    'confidence': 0.5,
                    'reason': f'Ambiguous classification: {best_category} and {sorted_categories[1][0]} are too similar',
                    'method': 'hybrid',
                    'keyword_score': keyword_score if best_keyword_category else 0.0,
                    'semantic_score': semantic_scores.get(best_category, 0.0),
                    'scores_by_category': combined_scores
                }
            # Low confidence but not ambiguous
            return {
                'category': 'Other',
                'confidence': 0.5,
                'reason': f'Low confidence in {best_category}. Requires manual review.',
                'method': 'hybrid',
                'keyword_score': keyword_score if best_keyword_category else 0.0,
                'semantic_score': semantic_scores.get(best_category, 0.0),
                'scores_by_category': combined_scores
            }

        # High confidence - return best match
        reason = f'Hybrid classification: keyword + semantic match for {best_category}'
        if best_keyword_category == best_category and keyword_reason:
            # Include the specific keyword that matched
            reason = keyword_reason
        return {
            'category': best_category,
            'confidence': best_confidence,
            'reason': reason,
            'method': 'hybrid',
            'keyword_score': keyword_score if best_keyword_category else 0.0,
            'semantic_score': semantic_scores.get(best_category, 0.0),
            'scores_by_category': combined_scores
        }
