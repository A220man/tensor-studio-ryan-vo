interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({ page, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  const pages = [];
  const start = Math.max(1, page - 2);
  const end = Math.min(totalPages, page + 2);
  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  return (
    <div className="flex-between mt-4">
      <button
        className="btn"
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
      >
        Previous
      </button>
      <div style={{ display: "flex", gap: "0.5rem" }}>
        {pages.map((p) => (
          <button
            key={p}
            className={`btn ${p === page ? "btn-primary" : ""}`}
            onClick={() => onPageChange(p)}
          >
            {p}
          </button>
        ))}
      </div>
      <button
        className="btn"
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
      >
        Next
      </button>
    </div>
  );
}