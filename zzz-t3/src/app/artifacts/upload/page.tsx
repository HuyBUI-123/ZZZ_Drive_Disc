import { redirect } from "next/navigation";
import { auth } from "~/server/auth";
import ArtifactUploadForm from "./ArtifactUploadForm";

export default async function ArtifactUploadPage() {
  const session = await auth();

  if (!session) {
    redirect("/api/auth/signin");
  }

  return (
    <main className="min-h-screen pb-20 pt-8 text-white">
      <div className="container mx-auto px-4">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
            Upload <span className="text-yellow-500">Drive Discs</span>
          </h1>
          <p className="mt-4 text-lg text-gray-300">
            Import a JSON file exported from the scanner to add many drive discs at once
          </p>
        </div>

        <ArtifactUploadForm />
      </div>
    </main>
  );
}
