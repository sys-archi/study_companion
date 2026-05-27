from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.documents.forms import DocumentUploadForm
from apps.documents.models import Document
from services.document_service import delete_document, process_document


@login_required
def upload_view(request):
    if request.method == "POST":
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            document.status = Document.STATUS_PENDING
            document.save()
            process_document(document.id)
            document.refresh_from_db()
            if document.status == Document.STATUS_READY:
                messages.success(request, f'"{document.title}" is ready for study!')
            else:
                messages.error(
                    request,
                    f'Processing failed: {document.error_message or "Unknown error"}',
                )
            return redirect("documents:detail", pk=document.pk)
    else:
        form = DocumentUploadForm()
    return render(request, "documents/upload.html", {"form": form})


@login_required
def list_view(request):
    documents = Document.objects.filter(user=request.user)
    return render(request, "documents/list.html", {"documents": documents})


@login_required
def detail_view(request, pk):
    document = get_object_or_404(Document, pk=pk, user=request.user)
    return render(request, "documents/detail.html", {"document": document})


@login_required
def reprocess_view(request, pk):
    document = get_object_or_404(Document, pk=pk, user=request.user)
    process_document(document.id)
    document.refresh_from_db()
    messages.info(request, "Document reprocessed.")
    return redirect("documents:detail", pk=pk)


@login_required
@require_POST
def delete_view(request, pk):
    document = get_object_or_404(Document, pk=pk, user=request.user)
    title = document.title
    delete_document(document)
    messages.success(request, f'"{title}" was deleted.')
    return redirect("documents:list")
