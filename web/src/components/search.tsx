"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useDebounce } from "use-debounce";
import { getSearchResults } from "@/utils";

export default function Search() {
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearchTerm] = useDebounce(searchTerm, 300);

  const { data: searchResults, isLoading } = useQuery({
    queryKey: ["search", debouncedSearchTerm],
    queryFn: () => getSearchResults(debouncedSearchTerm),
    enabled: debouncedSearchTerm.length > 2,
  });

  return (
    <div className="w-full max-w-lg px-4 mt-4 fixed top-0 left-1/2 -translate-x-1/2 z-10">
      {/* Search Container */}
      <div className="w-full relative hover:scale-105 transition-all duration-300">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search lyrics..."
          className="w-full h-12 px-6 rounded-full 
                   bg-white/20 backdrop-blur-md
                   text-neutral-700 text-lg english
                   placeholder:text-neutral-500
                   focus:outline-none
                   shadow-[0_4px_15px_rgba(0,0,0,0.15)]
                   transition-all duration-300
                   hover:shadow-[0_6px_20px_rgba(0,0,0,0.2)]
                   focus:shadow-[0_6px_20px_rgba(0,0,0,0.2)]
                   border border-white/30"
        />

        {/* Search Icon */}
        <div className="absolute right-6 top-1/2 -translate-y-1/2 hover:animate-pulse">
          {isLoading ? (
            <div className="animate-spin">
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                className="text-neutral-400"
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
          ) : (
            <svg
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="none"
              className="text-neutral-400"
            >
              <path
                d="M9 17A8 8 0 1 0 9 1a8 8 0 0 0 0 16zM19 19l-4.35-4.35"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          )}
        </div>
      </div>

      {/* Search Results */}
      {debouncedSearchTerm.length > 2 && searchResults && (
        <div className="mt-4 bg-white/20 backdrop-blur-md rounded-2xl p-4 shadow-lg">
          {searchResults.slice(0, 3).map((result, index) => (
            <div key={index}>
              {index > 0 && <hr className="my-3 border-white/20" />}
              <div className="text-neutral-700">
                <h3 className="text-lg font-semibold">{result.title}</h3>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
