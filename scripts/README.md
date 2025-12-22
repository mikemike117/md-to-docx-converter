@"
# LaTeX to DOCX Converter

Конвертер документов из LaTeX в формат Word (.docx) с поддержкой изображений, таблиц и математических формул.

## Возможности

- Конвертация LaTeX → Markdown → DOCX
- Поддержка изображений и таблиц  
- Автоматическое разбиение на разделы
- Обработка математических формул

## Использование

\`\`\`bash
# Собрать DOCX из LaTeX
make docx

# Очистить сгенерированные файлы  
make clean
\`\`\`

Структура
- \`proba.tex\` - пример LaTeX документа
- \`scripts/latex_to_markdown.py\` - главный конвертер
- \`Makefile\` - автоматизация сборки
"@ | Out-File -FilePath README.md -Encoding utf8