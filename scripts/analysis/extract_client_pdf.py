import PyPDF2

with open('.context/Informe_de_Proyecto_renombre_archivos.pdf', 'rb') as f:
    reader = PyPDF2.PdfReader(f)
    text = ''
    for page in reader.pages:
        text += page.extract_text() + '\n'
    
    # Guardar a archivo para mejor lectura
    with open('.context/informe_extracted.txt', 'w', encoding='utf-8') as out:
        out.write(text)
    
    print(f"Páginas: {len(reader.pages)}")
    print(f"Caracteres: {len(text)}")
    print("\n" + "="*80)
    print("CONTENIDO:")
    print("="*80)
    print(text)
