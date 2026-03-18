import React, { useMemo, useState } from "react";

const promptSamples = [
  {
    text: "Write a to-do list for a personal project or task",
    icon: "list",
  },
  {
    text: "Generate an email reply to a job offer",
    icon: "mail",
  },
  {
    text: "Summarize meeting notes into action items",
    icon: "note",
  },
  {
    text: "Create a study plan for learning a new skill",
    icon: "spark",
  },
];

function LogoStarIcon({ className = "" }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
      <path
        d="M12 2.5L13.9 9.1L20.5 11L13.9 12.9L12 19.5L10.1 12.9L3.5 11L10.1 9.1L12 2.5Z"
        fill="currentColor"
      />
    </svg>
  );
}

function PlusIcon({ className = "" }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
      <path d="M12 5V19M5 12H19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function SearchIcon({ className = "" }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
      <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" />
      <path d="M20 20L16.65 16.65" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function HomeIcon({ className = "" }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
      <path
        d="M3 10.5L12 3L21 10.5V20C21 20.55 20.55 21 20 21H15V14H9V21H4C3.45 21 3 20.55 3 20V10.5Z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function FolderIcon({ className = "" }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
      <path
        d="M3 7C3 5.9 3.9 5 5 5H9L11 7H19C20.1 7 21 7.9 21 9V17C21 18.1 20.1 19 19 19H5C3.9 19 3 18.1 3 17V7Z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function HistoryIcon({ className = "" }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
      <path d="M3 12C3 7.03 7.03 3 12 3C16.97 3 21 7.03 21 12C21 16.97 16.97 21 12 21" stroke="currentColor" strokeWidth="2" />
      <path d="M3 4V9H8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 7V12L15 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function SettingsIcon({ className = "" }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
      <path
        d="M12 15.2C13.77 15.2 15.2 13.77 15.2 12C15.2 10.23 13.77 8.8 12 8.8C10.23 8.8 8.8 10.23 8.8 12C8.8 13.77 10.23 15.2 12 15.2Z"
        stroke="currentColor"
        strokeWidth="2"
      />
      <path
        d="M19.4 15L21 16.2L19.2 19.2L17.3 18.4C16.9 18.7 16.4 19 15.9 19.2L15.6 21.2H12.4L12.1 19.2C11.6 19 11.1 18.8 10.7 18.4L8.8 19.2L7 16.2L8.6 15C8.6 14.7 8.5 14.3 8.5 14C8.5 13.7 8.5 13.3 8.6 13L7 11.8L8.8 8.8L10.7 9.6C11.1 9.3 11.6 9 12.1 8.8L12.4 6.8H15.6L15.9 8.8C16.4 9 16.9 9.2 17.3 9.6L19.2 8.8L21 11.8L19.4 13C19.4 13.3 19.5 13.7 19.5 14C19.5 14.3 19.5 14.7 19.4 15Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function SendArrowIcon({ className = "" }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
      <path d="M5 12H19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M13 6L19 12L13 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function CardIcon({ type, className = "" }) {
  if (type === "mail") {
    return (
      <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
        <rect x="3" y="5" width="18" height="14" rx="2" stroke="currentColor" strokeWidth="2" />
        <path d="M4 7L12 13L20 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }

  if (type === "note") {
    return (
      <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
        <rect x="5" y="3" width="14" height="18" rx="2" stroke="currentColor" strokeWidth="2" />
        <path d="M9 8H15M9 12H15M9 16H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
    );
  }

  if (type === "spark") {
    return (
      <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
        <path d="M12 3L13.4 8.6L19 10L13.4 11.4L12 17L10.6 11.4L5 10L10.6 8.6L12 3Z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
      <path d="M8 7H19M8 12H19M8 17H19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <circle cx="5" cy="7" r="1" fill="currentColor" />
      <circle cx="5" cy="12" r="1" fill="currentColor" />
      <circle cx="5" cy="17" r="1" fill="currentColor" />
    </svg>
  );
}

function Sidebar() {
  return (
    <aside className="fixed left-6 top-6 hidden h-[calc(100vh-48px)] w-[64px] flex-col rounded-2xl bg-white p-3 shadow-sm lg:flex">
      <div className="flex flex-col items-center gap-4">
        <button className="flex h-10 w-10 items-center justify-center rounded-xl text-[#7C3AED] hover:bg-[#F6F2FF]" aria-label="AAF-AIOS logo">
          <LogoStarIcon className="h-5 w-5" />
        </button>
        <button className="flex h-10 w-10 items-center justify-center rounded-xl text-neutral-700 hover:bg-neutral-100" aria-label="New Chat">
          <PlusIcon className="h-5 w-5" />
        </button>
      </div>

      <div className="mt-8 flex flex-1 flex-col items-center gap-3">
        <button className="flex h-10 w-10 items-center justify-center rounded-xl text-neutral-600 hover:bg-neutral-100" aria-label="Search">
          <SearchIcon className="h-5 w-5" />
        </button>
        <button className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#F6F2FF] text-[#7C3AED]" aria-label="Home">
          <HomeIcon className="h-5 w-5" />
        </button>
        <button className="flex h-10 w-10 items-center justify-center rounded-xl text-neutral-600 hover:bg-neutral-100" aria-label="Folder">
          <FolderIcon className="h-5 w-5" />
        </button>
        <button className="flex h-10 w-10 items-center justify-center rounded-xl text-neutral-600 hover:bg-neutral-100" aria-label="History">
          <HistoryIcon className="h-5 w-5" />
        </button>
      </div>

      <div className="flex flex-col items-center gap-3">
        <button className="flex h-10 w-10 items-center justify-center rounded-xl text-neutral-600 hover:bg-neutral-100" aria-label="Settings">
          <SettingsIcon className="h-5 w-5" />
        </button>
        <div className="h-10 w-10 rounded-full bg-gradient-to-br from-[#A855F7] to-[#EC4899]" aria-label="User avatar" />
      </div>
    </aside>
  );
}

function GreetingSection({ name = "Linh" }) {
  return (
    <section className="space-y-2">
      <h1 className="text-5xl font-semibold tracking-tight text-black">
        Hi there, <span className="bg-gradient-to-r from-[#A855F7] to-[#EC4899] bg-clip-text text-transparent">{name}</span>
      </h1>
      <h2 className="text-5xl font-semibold tracking-tight text-black">What would you like to know?</h2>
      <p className="pt-2 text-sm text-neutral-500">
        Use one of the most common prompts below or use your own to begin
      </p>
    </section>
  );
}

function PromptCard({ text, icon }) {
  return (
    <button className="flex h-[144px] w-full flex-col justify-between rounded-2xl bg-white p-5 text-left shadow-sm">
      <p className="text-[15px] leading-6 text-neutral-800">{text}</p>
      <CardIcon type={icon} className="h-5 w-5 text-neutral-500" />
    </button>
  );
}

function InputBox() {
  const [value, setValue] = useState("");

  const countText = useMemo(() => `${value.length}/1000`, [value.length]);

  return (
    <section className="w-full rounded-2xl bg-white p-4 shadow-sm">
      <div className="mb-3 flex justify-end">
        <button className="rounded-full border border-neutral-200 bg-white px-3 py-1 text-xs font-medium text-neutral-700">
          🌐 All Web ▾
        </button>
      </div>

      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value.slice(0, 1000))}
        placeholder="Ask whatever you want…"
        rows={4}
        className="w-full resize-none border-0 bg-transparent text-[15px] text-neutral-900 placeholder:text-neutral-400 focus:outline-none"
      />

      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center gap-4 text-sm text-neutral-600">
          <button className="hover:text-neutral-900">⊕ Add Attachment</button>
          <button className="hover:text-neutral-900">🖼 Use Image</button>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs text-neutral-500">{countText}</span>
          <button className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-[#7C3AED] text-white">
            <SendArrowIcon className="h-4 w-4" />
          </button>
        </div>
      </div>
    </section>
  );
}

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#F2F2F2] font-[DM_Sans,sans-serif]">
      <Sidebar />

      <main className="mx-auto flex min-h-screen w-full max-w-[1280px] items-center px-8 py-10 lg:pl-[120px]">
        <div className="w-full space-y-8">
          <GreetingSection name="Linh" />

          <section className="grid grid-cols-1 gap-4 lg:grid-cols-4">
            {promptSamples.map((item) => (
              <PromptCard key={item.text} text={item.text} icon={item.icon} />
            ))}
          </section>

          <button className="text-sm font-medium text-neutral-500 hover:text-neutral-700">⟳ Refresh Prompts</button>

          <InputBox />
        </div>
      </main>
    </div>
  );
}
