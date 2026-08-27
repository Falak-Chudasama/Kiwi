from pathlib import Path

from app.core.files import output_dir
from app.models.job import Job
from app.services import archives, compression, documents, images, pdf_tools, universal
from app.workers.queue import task_queue


def _paths(job: Job, key: str = "input_paths") -> list[Path]:
    return [Path(p) for p in job.payload[key]]


def handle_document_convert(job: Job) -> list[str]:
    return [str(p) for p in universal.convert_any(_paths(job)[0], job.payload["target_ext"], output_dir(job.workspace))]


def handle_image_convert(job: Job) -> list[str]:
    out_dir = output_dir(job.workspace)
    return [
        str(
            images.convert_image(
                p,
                job.payload["target_ext"],
                out_dir,
                width=job.payload.get("width"),
                height=job.payload.get("height"),
                fit_mode=job.payload.get("fit_mode", "contain"),
            )
        )
        for p in _paths(job)
    ]


def handle_pdf_merge(job: Job) -> list[str]:
    return [str(pdf_tools.merge_pdfs(_paths(job), output_dir(job.workspace)))]


def handle_pdf_split(job: Job) -> list[str]:
    ranges = [tuple(r) for r in job.payload["ranges"]]
    return [str(p) for p in pdf_tools.split_pdf(_paths(job)[0], output_dir(job.workspace), ranges)]


def handle_pdf_to_images(job: Job) -> list[str]:
    return [
        str(p)
        for p in pdf_tools.pdf_to_images(
            _paths(job)[0],
            output_dir(job.workspace),
            job.payload.get("image_format", "png"),
            dpi=int(job.payload.get("dpi", 150)),
        )
    ]


def handle_images_to_pdf(job: Job) -> list[str]:
    return [str(pdf_tools.images_to_pdf(_paths(job), output_dir(job.workspace)))]


def handle_pdf_rotate(job: Job) -> list[str]:
    return [str(pdf_tools.rotate_pdf(_paths(job)[0], output_dir(job.workspace), int(job.payload["degrees"]))) ]


def handle_pdf_reorder(job: Job) -> list[str]:
    return [str(pdf_tools.reorder_pdf(_paths(job)[0], output_dir(job.workspace), job.payload["order"]))]


def handle_pdf_protect(job: Job) -> list[str]:
    return [str(pdf_tools.protect_pdf(_paths(job)[0], output_dir(job.workspace), job.payload["password"]))]


def handle_pdf_unlock(job: Job) -> list[str]:
    return [str(pdf_tools.unlock_pdf(_paths(job)[0], output_dir(job.workspace), job.payload["password"]))]


def handle_pdf_watermark(job: Job) -> list[str]:
    return [
        str(
            pdf_tools.watermark_pdf(
                _paths(job)[0],
                output_dir(job.workspace),
                job.payload["text"],
                fontsize=int(job.payload.get("fontsize", 40)),
                opacity=float(job.payload.get("opacity", 0.25)),
                angle=int(job.payload.get("angle", 35)),
                position=job.payload.get("position", "center"),
                color=tuple(job.payload.get("color", [120, 120, 120])),
            )
        )
    ]


def handle_pdf_ocr(job: Job) -> list[str]:
    return [str(pdf_tools.ocr_pdf(_paths(job)[0], output_dir(job.workspace), job.payload.get("language", "eng")))]


def handle_compress_file(job: Job) -> list[str]:
    return [str(compression.compress_file(_paths(job)[0], output_dir(job.workspace), compression.CompressionLevel(job.payload["level"])))]


def handle_archive_create(job: Job) -> list[str]:
    return [
        str(
            archives.create_archive(
                _paths(job),
                output_dir(job.workspace),
                job.payload["archive_format"],
                job.payload.get("name"),
            )
        )
    ]


def handle_archive_extract(job: Job) -> list[str]:
    return [str(p) for p in archives.extract_archive(_paths(job)[0], output_dir(job.workspace))]


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
