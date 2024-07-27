import markdown2
from weasyprint import HTML
import re

def convert_to_pdf(file_path):
    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Final Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                font-size: 12px;
            }}
            h1 {{
                font-size: 24px;
                font-weight: bold;
                page-break-before: always;
            }}
            h2, h3, h4, h5, h6 {{
                font-size: 14px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 9px;
            }}
            th, td {{
                border: 1px solid black;
                padding: 5px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            .page-break {{
                page-break-before: always;
            }}
        </style>
    </head>
    <body>
        {content}
    </body>
    </html>
    '''

    with open(file_path, 'r') as file:
        content = file.read()

    # Convert content based on file type
    if file_path.endswith(('.md', '.txt', '.log')):
        # Pre-process the content to handle page breaks and titles
        content = preprocess_content(content)
        html_content = markdown2.markdown(content, extras=["tables"])
    else:
        raise ValueError("Unsupported file type. Please provide a '.md', '.txt', or '.log' file.")

    html_full = html_template.format(content=html_content)
    pdf_file_path = file_path.rsplit('.', 1)[0] + '.pdf'
    HTML(string=html_full).write_pdf(pdf_file_path)
    print(f"PDF generated at: {pdf_file_path}")

def preprocess_content(content):
    # Split content into lines
    lines = content.split('\n')
    processed_lines = []
    
    for line in lines:
        # Remove "Assistant:" prefix
        line = re.sub(r'^Assistant:\s*', '', line)
        
        # Handle page breaks and titles
        if line.startswith('### '):
            title = line[4:].strip()
            processed_lines.append('<div class="page-break"></div>')
            processed_lines.append(f'# {title}')
        else:
            processed_lines.append(line)
    
    return '\n'.join(processed_lines)

if __name__ == "__main__":
    file_path = input("Enter the path to the Markdown, Text, or Log file: ")
    convert_to_pdf(file_path)