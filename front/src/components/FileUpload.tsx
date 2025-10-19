export default function FileUpload({ onCodeLoaded }) {
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const codeText = e.target.result;
      onCodeLoaded(codeText);
    };
    reader.readAsText(file);
  };

  return (
    <div className="flex flex-col items-center gap-4">
      <label
        htmlFor="file-upload"
        className="cursor-pointer bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-xl"
      >
        Import
      </label>
      <input
        id="file-upload"
        type="file"
        accept=".py"
        onChange={handleFileChange}
        className="hidden"
      />
    </div>
  );
}
