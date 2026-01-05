import { render, screen } from '@testing-library/react';
import Page from './page';

describe('Page', () => {
  it('renders the dashboard', () => {
    render(<Page />);

    // Check for a heading that exists in the component
    const heading = screen.getByRole('heading', { name: /Total Revenue/i });

    expect(heading).toBeInTheDocument();
  });

  it('renders the Control and Command buttons', () => {
    render(<Page />);

    expect(screen.getByRole('button', { name: /Control/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Command/i })).toBeInTheDocument();
  });
});
