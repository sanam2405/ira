"use client";

import { getSearchResults } from "@/utils";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useDebounce } from "use-debounce";

const MAX_THRESHOLD = 4;

export default function Search() {
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearchTerm] = useDebounce(searchTerm, 300);
  const [selectedIndex, setSelectedIndex] = useState(-1);

  const { data: searchResults, isLoading } = useQuery({
    queryKey: ["search", debouncedSearchTerm],
    queryFn: () => getSearchResults(debouncedSearchTerm),
    enabled: debouncedSearchTerm.length > 2,
  });

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!searchResults?.length) return;

    switch (e.key) {
      case "Escape":
        e.preventDefault();
        setSearchTerm("");
        setSelectedIndex(-1);
        break;
      case "ArrowDown":
        e.preventDefault();
        setSelectedIndex((prev) => (prev >= MAX_THRESHOLD - 1 ? 0 : prev + 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        setSelectedIndex((prev) => (prev <= 0 ? MAX_THRESHOLD - 1 : prev - 1));
        break;
      case "Enter":
        if (selectedIndex >= 0) {
          const selectedResult = searchResults[selectedIndex];
          console.log(selectedResult);
          // TODO: Navigate to selectedResult
        }
        break;
    }
  };

  return (
    <div className="w-full max-w-lg px-4 mt-8 fixed top-0 left-1/2 -translate-x-1/2 z-10">
      {/* Search Container */}
      <div className="w-full relative hover:scale-105 transition-all duration-300">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Search lyrics..."
          className="w-full h-12 px-6 rounded-full 
                   bg-white/20 backdrop-blur-md
                   text-neutral-700 text-lg english
                   placeholder:text-neutral-900
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
          ) : (
            <svg
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="none"
              className="text-neutral-900"
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
        <div className="mt-4 bg-white/20 backdrop-blur-md rounded-2xl p-4 shadow-lg group">
          {searchResults.slice(0, MAX_THRESHOLD).map((result, index) => (
            <div key={index}>
              {index > 0 && <hr className="border-gray-200/50" />}
              <div
                className={`
                  cursor-pointer rounded-lg p-3 transition-all duration-200
                  ${index === selectedIndex ? "bg-amber-600/20 scale-105" : "hover:bg-amber-600/20 hover:scale-105"}
                  group-hover:[&:not(:hover)]:opacity-30
                  hover:opacity-100
                `}
              >
                <div className="text-gray-800">
                  <h3 className="text-lg font-semibold">{result.title}</h3>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
