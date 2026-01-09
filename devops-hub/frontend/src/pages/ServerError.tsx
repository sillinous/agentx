import { Link } from 'react-router-dom';
import { Button, Card } from '../components/ui';

interface ServerErrorProps {
  error?: Error;
  resetErrorBoundary?: () => void;
}

export default function ServerError({ error, resetErrorBoundary }: ServerErrorProps) {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <Card padding="lg" className="max-w-md w-full text-center">
        <div className="mb-6">
          <span className="text-6xl font-bold text-red-300">500</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Server Error</h1>
        <p className="text-gray-600 mb-4">
          Something went wrong on our end. Please try again later.
        </p>
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-700 font-mono">{error.message}</p>
          </div>
        )}
        <div className="flex justify-center gap-3">
          {resetErrorBoundary ? (
            <Button onClick={resetErrorBoundary}>Try Again</Button>
          ) : (
            <Button onClick={() => window.location.reload()}>Reload Page</Button>
          )}
          <Link to="/">
            <Button variant="secondary">Go to Dashboard</Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}
