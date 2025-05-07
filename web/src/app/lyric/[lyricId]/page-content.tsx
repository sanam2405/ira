"use client";

import { getSongDetails } from "@/utils";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

export default function PageContent() {
  const params = useParams();
  const lyricId = params.lyricId as string;

  const { data: song, isLoading } = useQuery({
    queryKey: ["song", lyricId],
    queryFn: () => getSongDetails(lyricId),
    enabled: !!lyricId,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin">
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            className="text-neutral-900"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        </div>
      </div>
    );
  }

  if (!song) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-lg text-neutral-900">Song not found</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-2xl mx-auto px-4 py-8">
      <div className="bg-white/20 backdrop-blur-md rounded-2xl p-6 shadow-lg">
        <h1 className="text-2xl font-bold mb-4">{song.title}</h1>

        {/* Lyrics */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-2">Lyrics</h2>
          <div className="whitespace-pre-line">{song.lyrics}</div>
        </div>

        {/* Metadata */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-2">Details</h2>
          <div className="space-y-2">
            {Object.entries(song.metadata).map(([key, value]) => (
              <div key={key} className="flex">
                <span className="font-medium w-1/3">{key}:</span>
                <span className="w-2/3">{value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Citations */}
        {song.citations && song.citations.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold mb-2">Citations</h2>
            <div className="space-y-4">
              {song.citations.map((citation, index) => (
                <div key={index} className="text-sm italic">
                  {citation}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
