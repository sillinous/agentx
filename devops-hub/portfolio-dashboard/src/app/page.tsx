import { fetchPortfolioSummary, fetchHealthStatus } from "@/lib/api";
import ProjectCard from "@/components/ProjectCard";
import RevenueOverview from "@/components/RevenueOverview";
import NextActions from "@/components/NextActions";
import StatusIndicator from "@/components/StatusIndicator";

export const revalidate = 30; // Revalidate every 30 seconds

export default async function Home() {
  const [portfolioData, healthData] = await Promise.all([
    fetchPortfolioSummary(),
    fetchHealthStatus(),
  ]);

  return (
    <main className="min-h-screen bg-black">
      {/* Header */}
      <header className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-lg sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="font-display text-4xl lg:text-5xl font-extrabold mb-2">
                <span className="text-gradient">Portfolio Command Center</span>
              </h1>
              <p className="text-zinc-400 text-sm font-mono">
                Real-time project status · Revenue tracking · Strategic insights
              </p>
            </div>
            <StatusIndicator
              apiHealthy={healthData.api_healthy}
              lastUpdated={portfolioData.last_updated}
            />
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-12 space-y-12">
        {/* Revenue Overview */}
        <section className="animate-fade-in">
          <RevenueOverview revenue={portfolioData.revenue} />
        </section>

        {/* Next Actions */}
        <section className="animate-fade-in" style={{ animationDelay: "0.1s" }}>
          <NextActions actions={portfolioData.next_actions} />
        </section>

        {/* Projects Grid */}
        <section>
          <h2 className="font-display text-3xl font-bold mb-6">
            Active Projects
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {portfolioData.projects
              .sort((a, b) => a.priority - b.priority)
              .map((project, index) => (
                <ProjectCard key={project.name} project={project} index={index} />
              ))}
          </div>
        </section>

        {/* Footer */}
        <footer className="text-center text-zinc-600 text-sm font-mono pt-12 border-t border-zinc-900">
          <p>
            Dashboard updates every 30 seconds · Data from DevOps Hub API
          </p>
          <p className="mt-2">
            Last updated: {new Date(portfolioData.last_updated).toLocaleString()}
          </p>
        </footer>
      </div>
    </main>
  );
}
