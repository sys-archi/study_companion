from django import forms

from apps.documents.models import Document


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["title", "subject", "doc_type", "file", "text_content"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-input", "placeholder": "e.g. Grade 10 Biology Chapter 3"}),
            "subject": forms.TextInput(attrs={"class": "form-input", "placeholder": "e.g. Biology"}),
            "doc_type": forms.Select(attrs={"class": "form-input", "id": "doc-type-select"}),
            "file": forms.FileInput(attrs={"class": "form-input", "id": "file-input"}),
            "text_content": forms.Textarea(
                attrs={
                    "class": "form-input",
                    "rows": 8,
                    "placeholder": "Paste your notes here...",
                    "id": "text-content-field",
                }
            ),
        }

    def clean(self):
        cleaned = super().clean()
        doc_type = cleaned.get("doc_type")
        file = cleaned.get("file")
        text = cleaned.get("text_content", "").strip()

        if doc_type == Document.TYPE_PDF and not file:
            raise forms.ValidationError("Please upload a PDF file.")
        if doc_type == Document.TYPE_TEXT and not text and not file:
            raise forms.ValidationError("Please paste text notes or upload a .txt file.")
        return cleaned
