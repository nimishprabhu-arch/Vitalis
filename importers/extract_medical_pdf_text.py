from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_FOLDER = ROOT / "data" / "medical_reports" / "raw"
PROCESSED_FOLDER = ROOT / "data" / "medical_reports" / "processed"


def extract_with_pypdf(pdf_path):
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    pages = []

    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(f"\n\n--- Page {index} ---\n\n{text}")

    return "".join(pages).strip()


def write_text_safely(output_path, content):
    safe_text = content.encode(
        "utf-8",
        errors="replace",
    ).decode("utf-8")

    output_path.write_text(
        safe_text,
        encoding="utf-8",
        errors="replace",
    )


def main():
    PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(RAW_FOLDER.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in: {RAW_FOLDER}")
        return

    extracted_count = 0
    failed_count = 0

    for pdf_path in pdf_files:
        output_path = PROCESSED_FOLDER / f"{pdf_path.stem}.txt"

        try:
            text = extract_with_pypdf(pdf_path)

            if not text:
                text = "[No extractable text found. This may be a scanned/image PDF.]"

            write_text_safely(
                output_path,
                f"source_file={pdf_path.name}\n{text}\n",
            )

            extracted_count += 1
            print(f"Extracted: {pdf_path.name} -> {output_path.name}")
        except Exception as error:
            failed_count += 1
            print(f"Failed: {pdf_path.name}")
            print(f"Reason: {error}")

    print("--------------------------------")
    print("Medical PDF text extraction complete.")
    print(f"Extracted PDFs: {extracted_count}")
    print(f"Failed PDFs: {failed_count}")


if __name__ == "__main__":
    main()