from docling.document_converter import DocumentConverter

source ="/home/test3/Documents/pdf/VEGA-Banc-Besoin_Materiel_banc -A.pdf"

converter = DocumentConverter()
result = converter.convert(source)

print(result.document.export_to_markdown())