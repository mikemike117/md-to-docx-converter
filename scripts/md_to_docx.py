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
    # БАЗА ДАННЫХ ПОЛНЫХ БИБЛИОГРАФИЧЕСКИХ ЗАПИСЕЙ
    full_citation_db = {
        # Основные 4 записи, которые у вас уже есть
        "sutskever2014sequence": "Ilya Sutskever, Oriol Vinyals, and Quoc VV Le. Sequence to sequence learning with neural networks. In Advances in Neural Information Processing Systems, pages 3104–3112, 2014.",
        "hochreiter1997long": "Sepp Hochreiter and Jürgen Schmidhuber. Long short-term memory. Neural computation, 9(8):1735–1780, 1997.",
        "bahdanau2014neural": "Dzmitry Bahdanau, Kyunghyun Cho, and Yoshua Bengio. Neural machine translation by jointly learning to align and translate. CoRR, abs/1409.0473, 2014.",
        "vaswani2017attention": "Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, and Illia Polosukhin. Attention Is All You Need. In Advances in Neural Information Processing Systems, pages 5998–6008, 2017.",
        
        # Остальные 36 записей из списка
        "ba2016layer": "Jimmy Lei Ba, Jamie Ryan Kiros, and Geoffrey E Hinton. Layer normalization. arXiv preprint arXiv:1607.06450, 2016.",
        "britz2017massive": "Denny Britz, Anna Goldie, Minh-Thang Luong, and Quoc V. Le. Massive exploration of neural machine translation architectures. CoRR, abs/1703.03906, 2017.",
        "cheng2016long": "Jianpeng Cheng, Li Dong, and Mirella Lapata. Long short-term memory-networks for machine reading. arXiv preprint arXiv:1601.06733, 2016.",
        "cho2014learning": "Kyunghyun Cho, Bart van Merrienboer, Caglar Gulcehre, Fethi Bougares, Holger Schwenk, and Yoshua Bengio. Learning phrase representations using rnn encoder-decoder for statistical machine translation. CoRR, abs/1406.1078, 2014.",
        "chollet2016xception": "Francois Chollet. Xception: Deep learning with depthwise separable convolutions. arXiv preprint arXiv:1610.02357, 2016.",
        "chung2014empirical": "Junyoung Chung, Çaglar Gülçehre, Kyunghyun Cho, and Yoshua Bengio. Empirical evaluation of gated recurrent neural networks on sequence modeling. CoRR, abs/1412.3555, 2014.",
        "dyer2016recurrent": "Chris Dyer, Adhiguna Kuncoro, Miguel Ballesteros, and Noah A. Smith. Recurrent neural network grammars. In Proc. of NAACL, 2016.",
        "gehring2017convolutional": "Jonas Gehring, Michael Auli, David Grangier, Denis Yarats, and Yann N. Dauphin. Convolutional sequence to sequence learning. arXiv preprint arXiv:1705.03122v2, 2017.",
        "graves2013generating": "Alex Graves. Generating sequences with recurrent neural networks. arXiv preprint arXiv:1308.0850, 2013.",
        "he2016deep": "Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun. Deep residual learning for image recognition. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition, pages 770–778, 2016.",
        "hochreiter2001gradient": "Sepp Hochreiter, Yoshua Bengio, Paolo Frasconi, and Jürgen Schmidhuber. Gradient flow in recurrent nets: the difficulty of learning long-term dependencies, 2001.",
        "huang2009self": "Zhongqiang Huang and Mary Harper. Self-training PCFG grammars with latent annotations across languages. In Proceedings of the 2009 Conference on Empirical Methods in Natural Language Processing, pages 832–841. ACL, August 2009.",
        "jozefowicz2016exploring": "Rafal Jozefowicz, Oriol Vinyals, Mike Schuster, Noam Shazeer, and Yonghui Wu. Exploring the limits of language modeling. arXiv preprint arXiv:1602.02410, 2016.",
        "kaiser2016can": "Łukasz Kaiser and Samy Bengio. Can active memory replace attention? In Advances in Neural Information Processing Systems, (NIPS), 2016.",
        "kaiser2016neural": "Łukasz Kaiser and Ilya Sutskever. Neural GPUs learn algorithms. In International Conference on Learning Representations (ICLR), 2016.",
        "kalchbrenner2017neural": "Nal Kalchbrenner, Lasse Espeholt, Karen Simonyan, Aaron van den Oord, Alex Graves, and Koray Kavukcuoglu. Neural machine translation in linear time. arXiv preprint arXiv:1610.10099v2, 2017.",
        "kim2017structured": "Yoon Kim, Carl Denton, Luong Hoang, and Alexander M. Rush. Structured attention networks. In International Conference on Learning Representations, 2017.",
        "kingma2015adam": "Diederik Kingma and Jimmy Ba. Adam: A method for stochastic optimization. In ICLR, 2015.",
        "kuchaiev2017factorization": "Oleksii Kuchaiev and Boris Ginsburg. Factorization tricks for LSTM networks. arXiv preprint arXiv:1703.10722, 2017.",
        "lin2017structured": "Zhouhan Lin, Minwei Feng, Cicero Nogueira dos Santos, Mo Yu, Bing Xiang, Bowen Zhou, and Yoshua Bengio. A structured self-attentive sentence embedding. arXiv preprint arXiv:1703.03130, 2017.",
        "luong2015multi": "Minh-Thang Luong, Quoc V. Le, Ilya Sutskever, Oriol Vinyals, and Lukasz Kaiser. Multi-task sequence to sequence learning. arXiv preprint arXiv:1511.06114, 2015.",
        "luong2015effective": "Minh-Thang Luong, Hieu Pham, and Christopher D Manning. Effective approaches to attention-based neural machine translation. arXiv preprint arXiv:1508.04025, 2015.",
        "marcus1993building": "Mitchell P Marcus, Mary Ann Marcinkiewicz, and Beatrice Santorini. Building a large annotated corpus of english: The penn treebank. Computational linguistics, 19(2):313–330, 1993.",
        "mcclosky2006effective": "David McClosky, Eugene Charniak, and Mark Johnson. Effective self-training for parsing. In Proceedings of the Human Language Technology Conference of the NAACL, Main Conference, pages 152–159. ACL, June 2006.",
        "parikh2016decomposable": "Ankur Parikh, Oscar Täckström, Dipanjan Das, and Jakob Uszkoreit. A decomposable attention model. In Empirical Methods in Natural Language Processing, 2016.",
        "paulus2017deep": "Romain Paulus, Caiming Xiong, and Richard Socher. A deep reinforced model for abstractive summarization. arXiv preprint arXiv:1705.04304, 2017.",
        "petrov2006learning": "Slav Petrov, Leon Barrett, Romain Thibaux, and Dan Klein. Learning accurate, compact, and interpretable tree annotation. In Proceedings of the 21st International Conference on Computational Linguistics and 44th Annual Meeting of the ACL, pages 433–440. ACL, July 2006.",
        "press2016using": "Ofir Press and Lior Wolf. Using the output embedding to improve language models. arXiv preprint arXiv:1608.05859, 2016.",
        "sennrich2015neural": "Rico Sennrich, Barry Haddow, and Alexandra Birch. Neural machine translation of rare words with subword units. arXiv preprint arXiv:1508.07909, 2015.",
        "shazeer2017outrageously": "Noam Shazeer, Azalia Mirhoseini, Krzysztof Maziarz, Andy Davis, Quoc Le, Geoffrey Hinton, and Jeff Dean. Outrageously large neural networks: The sparsely-gated mixture-of-experts layer. arXiv preprint arXiv:1701.06538, 2017.",
        "srivastava2014dropout": "Nitish Srivastava, Geoffrey E Hinton, Alex Krizhevsky, Ilya Sutskever, and Ruslan Salakhutdinov. Dropout: a simple way to prevent neural networks from overfitting. Journal of Machine Learning Research, 15(1):1929–1958, 2014.",
        "sukhbaatar2015end": "Sainbayar Sukhbaatar, Arthur Szlam, Jason Weston, and Rob Fergus. End-to-end memory networks. In C. Cortes, N. D. Lawrence, D. D. Lee, M. Sugiyama, and R. Garnett, editors, Advances in Neural Information Processing Systems 28, pages 2440–2448. Curran Associates, Inc., 2015.",
        "szegedy2015rethinking": "Christian Szegedy, Vincent Vanhoucke, Sergey Ioffe, Jonathon Shlens, and Zbigniew Wojna. Rethinking the inception architecture for computer vision. CoRR, abs/1512.00567, 2015.",
        "vinyals2015grammar": "Vinyals & Kaiser, Koo, Petrov, Sutskever, and Hinton. Grammar as a foreign language. In Advances in Neural Information Processing Systems, 2015.",
        "wu2016google": "Yonghui Wu, Mike Schuster, Zhifeng Chen, Quoc V Le, Mohammad Norouzi, Wolfgang Macherey, Maxim Krikun, Yuan Cao, Qin Gao, Klaus Macherey, et al. Google's neural machine translation system: Bridging the gap between human and machine translation. arXiv preprint arXiv:1609.08144, 2016.",
        "zhou2016deep": "Jie Zhou, Ying Cao, Xuguang Wang, Peng Li, and Wei Xu. Deep recurrent models with fast-forward connections for neural machine translation. CoRR, abs/1606.04199, 2016.",
        "zhu2013fast": "Muhua Zhu, Yue Zhang, Wenliang Chen, Min Zhang, and Jingbo Zhu. Fast and accurate shift-reduce constituent parsing. In Proceedings of the 51st Annual Meeting of the Association for Computational Linguistics, pages 434–443, 2013.",
    }
    
    # Находим все ссылки вида [@citation1, @citation2, ...]
    citation_pattern = re.compile(r'\[(@[^\]]+)\]')
    matches = citation_pattern.findall(text)
    
    # Собираем все уникальные ключи
    unique_citation_keys = set()
    
    for match in matches:
        # Разбиваем несколько ключей, если они есть
        keys = [key.strip().lstrip('@') for key in match.split(',')]
        unique_citation_keys.update(keys)
    
    if not unique_citation_keys:
        return text
    
    # Преобразуем в список для сохранения порядка
    unique_citation_keys = list(unique_citation_keys)
    
    # Создаем полноценный раздел "References" на английском
    references_section = "\n\n## References\n\n"
    
    # Заменяем ссылки в тексте
    def replace_citation(match):
        keys_text = match.group(1)  # Текст внутри скобок без внешних []
        keys = [key.strip().lstrip('@') for key in keys_text.split(',')]
        
        # Получаем номера для каждого ключа
        numbers = []
        for key in keys:
            if key in unique_citation_keys:
                number = unique_citation_keys.index(key) + 1
                numbers.append(str(number))
            else:
                numbers.append(f"??{key}??")
        
        return f"[{', '.join(numbers)}]"
    
    # Заменяем все ссылки
    text = citation_pattern.sub(replace_citation, text)
    
    # Добавляем записи в раздел литературы
    for i, cite_key in enumerate(unique_citation_keys, 1):
        if cite_key in full_citation_db:
            full_entry = full_citation_db[cite_key]
        else:
            full_entry = f"**{cite_key}** (full bibliographic description not found in database)"
        
        references_section += f"{i}. {full_entry}\n\n"
    
    # Добавляем раздел в конец документа, если его еще нет
    # Проверяем на разные варианты написания
    if not re.search(r'##\s*(References|Список литературы)', text, re.IGNORECASE):
        text += references_section
    else:
        # Если есть русская версия, заменяем ее на английскую
        text = re.sub(r'##\s*Список литературы', '## References', text, flags=re.IGNORECASE)
    
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

