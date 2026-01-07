// Barrel export for all components

// Navigation
export { NavBar, ModeToggle } from './NavBar';

// Dashboard components
export {
  KPICard,
  KPIRow,
  RevenueChart,
  ActivityFeed,
  ActivityFeedItem,
  ControlDashboard,
} from './Dashboard';
export type { KPIData, ActivityItem } from './Dashboard';

// Chat components
export {
  AGENTS,
  ChatMessage,
  ChatLoading,
  ChatHistory,
  AgentSelector,
  ChatInput,
  ChatPanel,
} from './Chat';
export type { AgentKey, Message } from './Chat';

// Canvas components
export { LiveCanvas } from './LiveCanvas';

// Conversation components
export { ConversationSidebar } from './ConversationSidebar';
