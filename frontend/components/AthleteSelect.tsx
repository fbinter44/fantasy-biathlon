"use client";

import { useState, useRef, useEffect } from "react";
import { AthleteResponse } from "@/lib/api";
import Flag from "@/components/Flag";

interface Props {
  athletes: AthleteResponse[];
  value: string;
  onChange: (ibuId: string) => void;
  exclude?: string[];
  disabled?: boolean;
  placeholder?: string;
}

function athleteName(a: AthleteResponse) {
  return `${a.family_name} ${a.given_name}`;
}

export default function AthleteSelect({
  athletes,
  value,
  onChange,
  exclude = [],
  disabled = false,
  placeholder = "Rechercher...",
}: Props) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [openUpward, setOpenUpward] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const selected = athletes.find((a) => a.ibu_id === value);

  const filtered = athletes
    .filter((a) => !exclude.includes(a.ibu_id))
    .filter((a) => athleteName(a).toLowerCase().includes(query.toLowerCase()))
    .slice(0, 50);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function openSearch() {
    if (disabled) return;
    if (ref.current) {
      const rect = ref.current.getBoundingClientRect();
      setOpenUpward(window.innerHeight - rect.bottom < 220);
    }
    setQuery("");
    setOpen(true);
    setTimeout(() => inputRef.current?.focus(), 0);
  }

  function handleSelect(ibuId: string) {
    onChange(ibuId);
    setQuery("");
    setOpen(false);
  }

  const baseClass = "w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500";

  return (
    <div ref={ref} className="relative">
      {/* Champ fermé — affiche drapeau + nom */}
      {!open && (
        <button
          type="button"
          onClick={openSearch}
          disabled={disabled}
          className={`${baseClass} text-left flex items-center gap-2 w-full ${
            disabled ? "bg-gray-100 text-gray-400 cursor-not-allowed" : "bg-white cursor-pointer hover:border-blue-400"
          }`}
        >
          {selected ? (
            <>
              <Flag nation={selected.nation} />
              <span>{athleteName(selected)}</span>
            </>
          ) : (
            <span className="text-gray-400">{placeholder}</span>
          )}
        </button>
      )}

      {/* Input de recherche — visible uniquement quand ouvert */}
      {open && (
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Rechercher..."
          className={`${baseClass} bg-white`}
        />
      )}

      {/* Dropdown */}
      {open && (
        <ul className={`absolute z-20 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-52 overflow-y-auto ${openUpward ? "bottom-full mb-1" : "top-full mt-1"}`}>
          <li
            onMouseDown={() => handleSelect("")}
            className="px-3 py-2 text-sm text-gray-400 hover:bg-gray-50 cursor-pointer"
          >
            — aucun —
          </li>
          {filtered.length === 0 ? (
            <li className="px-3 py-2 text-sm text-gray-400">Aucun résultat</li>
          ) : (
            filtered.map((a) => (
              <li
                key={a.ibu_id}
                onMouseDown={() => handleSelect(a.ibu_id)}
                className={`px-3 py-2 text-sm flex items-center gap-2 hover:bg-blue-50 cursor-pointer ${
                  a.ibu_id === value ? "bg-blue-50 font-medium" : ""
                }`}
              >
                <Flag nation={a.nation} />
                {athleteName(a)}
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}
