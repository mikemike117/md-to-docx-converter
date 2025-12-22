PYTHON_CMD := py -3
PANDOC ?= pandoc
MD_SRC := document.md  # ⬅️ Теперь входной Markdown файл
BUILD_DIR := build
DOCX := $(BUILD_DIR)/output.docx

.PHONY: all docx clean

all: docx

$(BUILD_DIR):
	@if not exist $(BUILD_DIR) mkdir $(BUILD_DIR)

docx: | $(BUILD_DIR)
	$(PYTHON_CMD) scripts/md_to_docx.py $(MD_SRC) $(DOCX)

clean:
	@if exist $(BUILD_DIR) rmdir /s /q $(BUILD_DIR)
	@if exist temp_md rmdir /s /q temp_md