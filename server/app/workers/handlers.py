from pathlib import Path

from app.core.files import output_dir
from app.models.job import Job
from app.services import archives, compression, documents, images, pdf_tools
from app.workers.queue import task_queue


def _paths(job: Job, key: str = "input_paths") -> list[Path]:
    return [Path(p) for p in job.payload[key]]


def handle_document_convert(job: Job) -> list[str]:
    out_dir = output_dir()
    input_path = _paths(job)[0]
    target_ext = job.payload["target_ext"]
    result = documents.convert_document(input_path, target_ext, out_dir)
    return [str(result)]


def handle_image_convert(job: Job) -> list[str]:
    out_dir = output_dir()
    target_ext = job.payload["target_ext"]
    results = [str(images.convert_image(p, target_ext, out_dir)) for p in _paths(job)]
    return results


def handle_pdf_merge(job: Job) -> list[str]:
    out_dir = output_dir()
    result = pdf_tools.merge_pdfs(_paths(job), out_dir)
    return [str(result)]


def handle_pdf_split(job: Job) -> list[str]:
    out_dir = output_dir()
    input_path = _paths(job)[0]
    ranges = [tuple(r) for r in job.payload["ranges"]]
    results = pdf_tools.split_pdf(input_path, out_dir, ranges)
    return [str(p) for p in results]


def handle_pdf_to_images(job: Job) -> list[str]:
    out_dir = output_dir()
    input_path = _paths(job)[0]
    image_format = job.payload.get("image_format", "png")
    results = pdf_tools.pdf_to_images(input_path, out_dir, image_format)
    return [str(p) for p in results]


def handle_images_to_pdf(job: Job) -> list[str]:
    out_dir = output_dir()
    result = pdf_tools.images_to_pdf(_paths(job), out_dir)
    return [str(result)]


def handle_pdf_rotate(job: Job) -> list[str]:
    out_dir = output_dir()
    input_path = _paths(job)[0]
    degrees = job.payload["degrees"]
    result = pdf_tools.rotate_pdf(input_path, out_dir, degrees)
    return [str(result)]


def handle_pdf_reorder(job: Job) -> list[str]:
    out_dir = output_dir()
    input_path = _paths(job)[0]
    order = job.payload["order"]
    result = pdf_tools.reorder_pdf(input_path, out_dir, order)
    return [str(result)]


def handle_pdf_protect(job: Job) -> list[str]:
    out_dir = output_dir()
    input_path = _paths(job)[0]
    password = job.payload["password"]
    result = pdf_tools.protect_pdf(input_path, out_dir, password)
    return [str(result)]


def handle_pdf_unlock(job: Job) -> list[str]:
    out_dir = output_dir()
    input_path = _paths(job)[0]
    password = job.payload["password"]
    result = pdf_tools.unlock_pdf(input_path, out_dir, password)
    return [str(result)]


def handle_pdf_watermark(job: Job) -> list[str]:
    out_dir = output_dir()
    input_path = _paths(job)[0]
    text = job.payload["text"]
    result = pdf_tools.watermark_pdf(input_path, out_dir, text)
    return [str(result)]


def handle_pdf_ocr(job: Job) -> list[str]:
    out_dir = output_dir()
    input_path = _paths(job)[0]
    language = job.payload.get("language", "eng")
    result = pdf_tools.ocr_pdf(input_path, out_dir, language)
    return [str(result)]


def handle_compress_file(job: Job) -> list[str]:
    out_dir = output_dir()
    input_path = _paths(job)[0]
    level = compression.CompressionLevel(job.payload["level"])
    result = compression.compress_file(input_path, out_dir, level)
    return [str(result)]


def handle_archive_create(job: Job) -> list[str]:
    out_dir = output_dir()
    archive_format = job.payload["archive_format"]
    name = job.payload.get("name", "archive")
    result = archives.create_archive(_paths(job), out_dir, archive_format, name)
    return [str(result)]


def handle_archive_extract(job: Job) -> list[str]:
    out_dir = output_dir()
    input_path = _paths(job)[0]
    results = archives.extract_archive(input_path, out_dir)
    return [str(p) for p in results]


def register_all_handlers() -> None:
    task_queue.register("document_convert", handle_document_convert)
    task_queue.register("image_convert", handle_image_convert)
    task_queue.register("pdf_merge", handle_pdf_merge)
    task_queue.register("pdf_split", handle_pdf_split)
    task_queue.register("pdf_to_images", handle_pdf_to_images)
    task_queue.register("images_to_pdf", handle_images_to_pdf)
    task_queue.register("pdf_rotate", handle_pdf_rotate)
    task_queue.register("pdf_reorder", handle_pdf_reorder)
    task_queue.register("pdf_protect", handle_pdf_protect)
    task_queue.register("pdf_unlock", handle_pdf_unlock)
    task_queue.register("pdf_watermark", handle_pdf_watermark)
    task_queue.register("pdf_ocr", handle_pdf_ocr)
    task_queue.register("compress_file", handle_compress_file)
    task_queue.register("archive_create", handle_archive_create)
    task_queue.register("archive_extract", handle_archive_extract)
