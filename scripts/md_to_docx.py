from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import List, Sequence, Tuple, Dict, Any
from dataclasses import dataclass
import subprocess
import json


@dataclass
class Section:
    title: str
    body: str


def normalize_whitespace(text: str) -> str:
    """Нормализация пробелов и переносов строк"""
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def extract_metadata(text: str) -> Tuple[Dict[str, str], str]:
    """Извлекает метаданные из начала Markdown файла (без YAML)"""
    metadata = {}
    
    # Простой формат: ключ: значение
    lines = text.split('\n')
    metadata_lines = []
    content_lines = []
    in_metadata = False
    
    for i, line in enumerate(lines):
        if i == 0 and line.strip() == '---':
            in_metadata = True
            continue
        elif in_metadata and line.strip() == '---':
            in_metadata = False
            continue
        elif in_metadata:
            metadata_lines.append(line)
        else:
            content_lines.append(line)
    
    # Парсим метаданные
    for line in metadata_lines:
        if ':' in line:
            key, value = line.split(':', 1)
            metadata[key.strip()] = value.strip().strip('"\'')
    
    return metadata, '\n'.join(content_lines)


def process_bibliography(text: str) -> str:
    """Обработка библиографических ссылок [@citation]"""
    
    # Находим все ссылки вида [@citation]
    citations = re.findall(r'\[@([^\]]+)\]', text)
    unique_citations = list(dict.fromkeys(citations))  # Уникальные ссылки
    
    if not unique_citations:
        return text
    
    # Создаем раздел References
    references_section = "\n\n## Список литературы\n\n"
    for i, cite in enumerate(unique_citations, 1):
        # Заменяем ссылки в тексте на номера
        text = re.sub(rf'\[@{re.escape(cite)}\]', f'[{i}]', text)
        # Добавляем в список литературы
        references_section += f"{i}. **{cite}**\n"
    
    # Добавляем раздел литературы в конец
    if not re.search(r'## Список литературы', text):
        text += references_section
    
    return text


def process_markdown_chunk(text: str) -> str:
    """Обработка одного куска Markdown"""
    transforms = [
        normalize_whitespace,
        process_bibliography,
    ]
    
    for transform in transforms:
        text = transform(text)
    
    return text


def split_into_sections(text: str) -> List[Section]:
    """Разбивает Markdown на разделы по заголовкам уровня 1"""
    sections: List[Section] = []
    
    lines = text.split('\n')
    current_title = ""
    current_body = []
    
    for line in lines:
        if line.startswith('# '):
            # Сохраняем предыдущий раздел
            if current_title or current_body:
                sections.append(Section(
                    title=current_title.lstrip('# ').strip(),
                    body='\n'.join(current_body).strip()
                ))
            # Начинаем новый раздел
            current_title = line
            current_body = []
        else:
            current_body.append(line)
    
    # Сохраняем последний раздел
    if current_title or current_body:
        sections.append(Section(
            title=current_title.lstrip('# ').strip() if current_title else "Основной текст",
            body='\n'.join(current_body).strip()
        ))
    
    # Если нет разделов, создаем один
    if not sections and text.strip():
        sections.append(Section("Документ", text.strip()))
    
    return sections


CYRILLIC_MAP = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "j", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "",
    "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def transliterate(text: str) -> str:
    """Транслитерация русских букв в латиницу"""
    pieces = []
    for ch in text.lower():
        pieces.append(CYRILLIC_MAP.get(ch, ch))
    return "".join(pieces)


def slugify(title: str, index: int) -> str:
    """Создание слага для имени файла"""
    slug = transliterate(title.strip())
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^a-z0-9\-]+", "", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return f"{index:02d}-{slug or 'section'}"


def write_sections(sections: Sequence[Section], output_dir: Path) -> List[Path]:
    """Запись разделов в отдельные Markdown файлы"""
    written: List[Path] = []
    
    for idx, section in enumerate(sections, start=1):
        md_path = output_dir / f"{slugify(section.title, idx)}.md"
        content = f"# {section.title}\n\n{section.body}"
        md_path.write_text(content, encoding="utf-8")
        written.append(md_path)
    
    return written


def write_toc(sections: Sequence[Section], output_dir: Path) -> Path:
    """Создание оглавления"""
    lines = ["# Оглавление", ""]
    
    for idx, section in enumerate(sections, start=1):
        file_name = slugify(section.title, idx) + ".md"
        lines.append(f"- [{section.title}]({file_name})")
    
    toc_path = output_dir / "00-oglavlenie.md"
    toc_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    
    return toc_path


def generate_docx_metadata(metadata: Dict[str, str]) -> str:
    """Генерация метаданных для Pandoc (без YAML)"""
    default_metadata = {
        'title': 'Мой документ',
        'author': 'Автор',
        'date': '2024',
        'lang': 'ru',
        'mainfont': 'Times New Roman',
    }
    
    # Объединяем с пользовательскими метаданными
    for key, value in metadata.items():
        if value:  # Не перезаписываем пустыми значениями
            default_metadata[key.lower()] = value
    
    # Создаем простой текстовый блок
    metadata_lines = ["---"]
    for key, value in default_metadata.items():
        if key in ['title', 'author', 'date']:
            metadata_lines.append(f'{key}: "{value}"')
    metadata_lines.append("---\n")
    
    return "\n".join(metadata_lines)


def convert_markdown_to_docx(input_path: Path, output_docx: Path, split: bool = False) -> bool:
    """Основная функция конвертации Markdown → DOCX"""
    
    try:
        # Чтение Markdown файла
        content = input_path.read_text(encoding="utf-8")
        
        # Извлекаем метаданные
        metadata, content = extract_metadata(content)
        
        # Обрабатываем контент
        processed_content = process_markdown_chunk(content)
        
        # Создаем папку для промежуточных файлов
        temp_dir = Path("temp_md")
        temp_dir.mkdir(exist_ok=True)
        
        if split:
            # Разбиваем на разделы
            sections = split_into_sections(processed_content)
            
            # Записываем разделы
            md_files = write_sections(sections, temp_dir)
            toc_file = write_toc(sections, temp_dir)
            
            # Собираем список файлов для Pandoc
            all_md_files = [str(toc_file)] + [str(f) for f in md_files]
        else:
            # Просто записываем весь контент в один файл
            single_file = temp_dir / "document.md"
            
            # Добавляем метаданные в начало
            full_content = generate_docx_metadata(metadata) + processed_content
            single_file.write_text(full_content, encoding="utf-8")
            
            all_md_files = [str(single_file)]
        
        # Запускаем Pandoc для создания DOCX
        cmd = ["pandoc", *all_md_files, "--resource-path=.", "-o", str(output_docx)]
        
        # Добавляем метаданные как аргументы командной строки
        if 'title' in metadata:
            cmd.extend(["--metadata", f"title={metadata['title']}"])
        if 'author' in metadata:
            cmd.extend(["--metadata", f"author={metadata['author']}"])
        
        # Добавляем язык и стили
        cmd.extend(["--metadata", f"lang={metadata.get('lang', 'ru')}"])
        cmd.extend(["--from", "markdown+smart"])
        
        # Запускаем Pandoc
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Ошибка Pandoc: {result.stderr}")
            return False
        
        print(f"✅ DOCX файл создан: {output_docx}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def parse_args() -> argparse.Namespace:
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description="Конвертер Markdown в Word документ (DOCX)"
    )
    parser.add_argument("input", type=Path, help="Путь к Markdown файлу (.md)")
    parser.add_argument("output", type=Path, help="Путь для выходного DOCX файла")
    parser.add_argument(
        "--no-split",
        action="store_true",
        help="Не разбивать на разделы; создать один DOCX файл"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Очистить временные файлы после конвертации"
    )
    return parser.parse_args()


def main() -> None:
    """Точка входа"""
    args = parse_args()
    
    # Проверяем входной файл
    if not args.input.exists():
        print(f"Файл не найден: {args.input}")
        return
    
    # Проверяем Pandoc
    try:
        subprocess.run(["pandoc", "--version"], capture_output=True, check=True)
    except:
        print("Pandoc не установлен или не найден в PATH")
        print("Скачайте с: https://pandoc.org/installing.html")
        return
    
    # Конвертируем
    success = convert_markdown_to_docx(args.input, args.output, split=not args.no_split)
    
    # Очищаем временные файлы если нужно
    if args.clean or success:
        temp_dir = Path("temp_md")
        if temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir)
    
    if success:
        print("Конвертация завершена успешно!")
    else:
        print("Конвертация не удалась")


if __name__ == "__main__":
    main()

