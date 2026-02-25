#ma venv c'est docenv
# from docling.document_converter import DocumentConverter

# def messi(source): 
   
#     converter = DocumentConverter()
#     result = converter.convert(source)
#     mark = result.document.export_to_markdown()

#     with open('fichier_markdown.txt', 'w', encoding='utf-8') as f:
#         f.write(mark)
#         print("ok")


# if __name__ == "__main__":
#     fichier_pdf = "Mail TALC SI.docx" 
#     messi(fichier_pdf)


from pdf2image import convert_from_path
import pytesseract

def extraction_tesseract(fichier_pdf):
    print(f"1. Découpage du PDF '{fichier_pdf}'...")
    pages = convert_from_path(fichier_pdf)
    texte_complet = ""

    print(f"2. Lecture par Tesseract ({len(pages)} pages)...")
    for index, page_img in enumerate(pages):
        print(f"-> Scan foudroyant de la page {index + 1}...")
        
        # Le scan OCR pur et dur (langue configurée sur Français + Anglais)
        texte = pytesseract.image_to_string(page_img, lang='fra+eng')
        
        texte_complet += f"\n\n=== PAGE {index + 1} ===\n{texte}\n"

    with open('resultat_tesseract.txt', 'w', encoding='utf-8') as f:
        f.write(texte_complet)
        print("\nVICTOIRE ! Terminé à la vitesse de l'éclair.")

if __name__ == "__main__":
    fichier_pdf = "CDC Arcelor mittal.pdf" 
    extraction_tesseract(fichier_pdf)