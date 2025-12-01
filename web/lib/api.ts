// 여러 파일 업로드 API
export async function uploadDocuments(files: File[]) {
    const formData = new FormData();

    files.forEach((file) => {
        formData.append("files", file);
    });

    const res = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
    });

    if (!res.ok) {
        throw new Error("업로드 실패 " + res.statusText);
    }

    return await res.json();
}
