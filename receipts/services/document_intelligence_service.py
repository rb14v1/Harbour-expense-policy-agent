from django.conf import settings
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, AnalyzeResult
from azure.core.credentials import AzureKeyCredential
from receipts.exceptions import DocumentExtractionError
import json


class DocumentIntelligenceService:
    def __init__(self):
        self.endpoint = settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT
        self.key = settings.AZURE_DOCUMENT_INTELLIGENCE_KEY
        self.client = DocumentIntelligenceClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key)
        )

    def analyze_receipt(self, content: bytes, content_type: str) -> dict:
        try:
            analyze_request = AnalyzeDocumentRequest(bytes_source=content)

            poller = self.client.begin_analyze_document(
                "prebuilt-receipt",
                analyze_request
            )
            result = poller.result()

            extracted = self._parse_result(result)
            return extracted

        except Exception as e:
            raise DocumentExtractionError(f"Failed to analyze receipt: {str(e)}")

    def _parse_result(self, result) -> dict:
        extracted = {
            "merchant": {
                "name": None,
                "address": None,
                "phone": None,
            },
            "invoice": {
                "invoice_number": None,
                "transaction_date": None,
            },
            "amounts": {
                "subtotal": None,
                "tax": None,
                "total": None,
                "currency": None,
            },
            "payment": {
                "method": None,
            },
            "line_items": [],
            "extraction": {
                "provider": "azure_ai_document_intelligence",
                "model": "prebuilt-receipt",
                "confidence": {},
            },
            "raw_response": None,
        }

        try:
            if result.documents:
                doc = result.documents[0]
                fields = doc.fields

                if 'MerchantName' in fields:
                    extracted['merchant']['name'] = fields['MerchantName'].value

                if 'MerchantAddress' in fields:
                    extracted['merchant']['address'] = fields['MerchantAddress'].value

                if 'MerchantPhoneNumber' in fields:
                    extracted['merchant']['phone'] = fields['MerchantPhoneNumber'].value

                if 'ReceiptNumber' in fields:
                    extracted['invoice']['invoice_number'] = fields['ReceiptNumber'].value

                if 'TransactionDate' in fields:
                    extracted['invoice']['transaction_date'] = str(fields['TransactionDate'].value) if fields['TransactionDate'].value else None

                if 'Subtotal' in fields and fields['Subtotal'].value:
                    extracted['amounts']['subtotal'] = float(fields['Subtotal'].value)

                if 'TotalTax' in fields and fields['TotalTax'].value:
                    extracted['amounts']['tax'] = float(fields['TotalTax'].value)

                if 'Total' in fields and fields['Total'].value:
                    extracted['amounts']['total'] = float(fields['Total'].value)

                if 'Currency' in fields:
                    extracted['amounts']['currency'] = fields['Currency'].value

                if 'PaymentMethod' in fields:
                    extracted['payment']['method'] = fields['PaymentMethod'].value

                if 'Items' in fields and fields['Items'].value:
                    for item in fields['Items'].value:
                        item_dict = {
                            "description": item.properties.get('Description', {}).value if 'Description' in item.properties else None,
                            "quantity": float(item.properties.get('Quantity', {}).value) if 'Quantity' in item.properties and item.properties['Quantity'].value else None,
                            "unit_price": float(item.properties.get('Price', {}).value) if 'Price' in item.properties and item.properties['Price'].value else None,
                            "amount": float(item.properties.get('TotalPrice', {}).value) if 'TotalPrice' in item.properties and item.properties['TotalPrice'].value else None,
                        }
                        extracted['line_items'].append(item_dict)

        except Exception as e:
            pass

        return extracted

    @staticmethod
    def _bytes_to_base64(data: bytes) -> str:
        import base64
        return base64.b64encode(data).decode('utf-8')
