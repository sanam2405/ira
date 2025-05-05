"use client";

export default function Search() {
  return (
    <div className="w-full max-w-2xl px-4 mt-auto mb-12">
      {/* Search Container */}
      <div className="w-full relative hover:scale-105 transition-all duration-300">
        <input
          type="text"
          placeholder="Search lyrics..."
          className="w-full h-14 px-6 rounded-full 
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
        </div>
      </div>
    </div>
  );
}
