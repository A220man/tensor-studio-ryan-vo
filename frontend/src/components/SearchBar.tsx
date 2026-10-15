import { useState, useEffect } from "react";

interface SearchBarProps {
  onSearch: (query: string) => void;
  placeholder?: string;
  initialValue?: string;
}

export default function SearchBar({
  onSearch,
  placeholder = "Search plugins...",
  initialValue = "",
}: SearchBarProps) {
  const [value, setValue] = useState(initialValue);

  useEffect(() => {
    const timer = setTimeout(() => {
      onSearch(value.trim());
    }, 300);
    return () => clearTimeout(timer);
  }, [value, onSearch]);

  return (
    <input
      type="text"
      className="input"
      value={value}
      placeholder={placeholder}
      onChange={(e) => setValue(e.target.value)}
    />
  );
}