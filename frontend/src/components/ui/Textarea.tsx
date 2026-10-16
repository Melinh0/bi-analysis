import { cn } from '../../lib/utils';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export function Textarea({
  label,
  error,
  helperText,
  className,
  id,
  ...props
}: TextareaProps) {
  const textareaId = id || props.name;

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={textareaId} className="block text-sm font-medium text-dark-700 mb-1.5">
          {label}
        </label>
      )}
      <textarea
        id={textareaId}
        className={cn(
          'w-full rounded-lg border bg-white px-4 py-2.5 text-sm placeholder:text-dark-400 resize-y min-h-[100px]',
          'focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-colors',
          error
            ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20'
            : 'border-dark-300 hover:border-dark-400 focus:border-primary-500',
          className
        )}
        aria-invalid={!!error}
        aria-describedby={error ? `${textareaId}-error` : helperText ? `${textareaId}-helper` : undefined}
        {...props}
      />
      {error && (
        <p id={`${textareaId}-error`} className="mt-1.5 text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
      {helperText && !error && (
        <p id={`${textareaId}-helper`} className="mt-1.5 text-sm text-dark-500">
          {helperText}
        </p>
      )}
    </div>
  );
}