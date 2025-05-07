"use client";

import { useScreenSize } from "@/hooks";
import { getSongDetails } from "@/utils";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";

export default function PageContent() {
  const params = useParams();
  const lyricId = params.lyricId as string;
  const screenSize = useScreenSize();

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

  const formatMetadataKey = (key: string) => {
    return key
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const isMobile = screenSize === "mobile";

  const HomeButton = () => (
    <Link
      href="/"
      className={`fixed top-2 right-2 z-50 w-10 h-10 flex items-center justify-center hover:scale-110 transition-all duration-300 ${
        isMobile ? "top-1 right-1" : "top-4 right-4"
      }`}
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={2}
        stroke="currentColor"
        className="w-6 h-6"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25"
        />
      </svg>
    </Link>
  );

  if (isMobile) {
    return (
      <>
        <HomeButton />
        <div className="w-full backdrop-blur-md bg-white/30 rounded-lg">
          <div className="flex flex-col w-full">
            {/* Title Section */}
            <div className="w-full p-8 my-4">
              <h1 className="text-3xl font-bold bengali">{song.title}</h1>
            </div>

            <hr className="w-1/2 mx-auto border-amber-900 animate-pulse" />

            {/* Lyrics Section */}
            <div className="w-full p-8">
              <div className="space-y-8">
                <div>
                  <h2 className="text-2xl font-semibold mb-6 bengali">
                    Lyrics
                  </h2>
                  <div className="whitespace-pre-line text-2xl leading-relaxed bengali">
                    {song.lyrics}
                  </div>
                </div>
              </div>
            </div>

            <hr className="w-1/2 mx-auto border-amber-900 animate-pulse" />

            {/* Details Section */}
            <div className="w-full p-8">
              <div className="space-y-10">
                {/* Metadata */}
                <div>
                  <h2 className="text-2xl font-semibold mb-6 english">
                    Details
                  </h2>
                  <div className="space-y-4">
                    {Object.entries(song.metadata).map(([key, value]) => (
                      <div key={key} className="flex flex-col space-y-1">
                        <span className="font-medium text-neutral-700 text-lg english">
                          {formatMetadataKey(key)}
                        </span>
                        <span className="text-neutral-900 text-xl bengali">
                          {value}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Citations */}
                {song.citations && song.citations.length > 0 && (
                  <div>
                    <h2 className="text-2xl font-semibold mb-6 english">
                      Citations
                    </h2>
                    <div className="space-y-4">
                      {song.citations.map((citation, index) => (
                        <div
                          key={index}
                          className="text-lg italic text-neutral-700 bengali"
                        >
                          {citation}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </>
    );
  }

  // Desktop layout
  return (
    <>
      <HomeButton />
      <div className="grid grid-cols-3 w-full">
        {/* Left Column - Metadata and Citations */}
        <div className="col-span-1 p-8">
          <h1 className="text-3xl font-bold mb-8 bengali">{song.title}</h1>
          <div className="space-y-10">
            {/* Metadata */}
            <div>
              <h2 className="text-2xl font-semibold mb-6 english">Details</h2>
              <div className="space-y-4">
                {Object.entries(song.metadata).map(([key, value]) => (
                  <div key={key} className="flex flex-col space-y-1">
                    <span className="font-medium text-neutral-700 text-lg english">
                      {formatMetadataKey(key)}
                    </span>
                    <span className="text-neutral-900 text-xl bengali">
                      {value}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Citations */}
            {song.citations && song.citations.length > 0 && (
              <div>
                <h2 className="text-2xl font-semibold mb-6 english">
                  Citations
                </h2>
                <div className="space-y-4">
                  {song.citations.map((citation, index) => (
                    <div
                      key={index}
                      className="text-lg italic text-neutral-700 bengali"
                    >
                      {citation}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Middle Column - Empty for background image */}
        <div className="col-span-1" />

        {/* Right Column - Lyrics */}
        <div className="col-span-1 p-8">
          <div className="space-y-8">
            <div>
              <h2 className="text-2xl font-semibold mb-6 bengali">Lyrics</h2>
              <div className="whitespace-pre-line text-2xl leading-relaxed bengali">
                {song.lyrics}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
