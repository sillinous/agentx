import { useState } from 'react';

interface RatingProps {
  value: number;
  onChange?: (rating: number) => void;
  readonly?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export default function Rating({ value, onChange, readonly = false, size = 'md' }: RatingProps) {
  const [hoverValue, setHoverValue] = useState(0);

  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  const displayValue = hoverValue || value;

  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          disabled={readonly}
          onClick={() => onChange?.(star)}
          onMouseEnter={() => !readonly && setHoverValue(star)}
          onMouseLeave={() => setHoverValue(0)}
          className={`${readonly ? 'cursor-default' : 'cursor-pointer'} focus:outline-none`}
        >
          <svg
            className={`${sizes[size]} ${
              star <= displayValue ? 'text-yellow-400' : 'text-gray-300'
            } transition-colors`}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        </button>
      ))}
    </div>
  );
}

export function RatingDisplay({ value, count }: { value: number | null; count?: number }) {
  if (value === null) {
    return <span className="text-gray-400 text-sm">No ratings yet</span>;
  }

  return (
    <div className="flex items-center gap-2">
      <Rating value={Math.round(value)} readonly size="sm" />
      <span className="text-sm text-gray-600">
        {value.toFixed(1)}
        {count !== undefined && <span className="text-gray-400"> ({count})</span>}
      </span>
    </div>
  );
}
