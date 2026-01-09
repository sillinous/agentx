import { Link } from 'react-router-dom';
import { Button, Card } from '../components/ui';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <Card padding="lg" className="max-w-md w-full text-center">
        <div className="mb-6">
          <span className="text-6xl font-bold text-gray-300">404</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Page Not Found</h1>
        <p className="text-gray-600 mb-6">
          The page you are looking for does not exist or has been moved.
        </p>
        <div className="flex justify-center gap-3">
          <Link to="/">
            <Button>Go to Dashboard</Button>
          </Link>
          <Button variant="secondary" onClick={() => window.history.back()}>
            Go Back
          </Button>
        </div>
      </Card>
    </div>
  );
}
