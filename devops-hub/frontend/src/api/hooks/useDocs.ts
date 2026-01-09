import { useQuery } from '@tanstack/react-query';
import client from '../client';
import type {
  DocumentationGuide,
  DocumentationExample,
  HandbookStructure,
  AgentDocumentation,
} from '../../types';

export function useHandbook() {
  return useQuery({
    queryKey: ['handbook'],
    queryFn: async () => {
      const { data } = await client.get<HandbookStructure>('/docs/handbook');
      return data;
    },
  });
}

export function useGuides(category?: string) {
  return useQuery({
    queryKey: ['guides', category],
    queryFn: async () => {
      const params = category ? { category } : {};
      const { data } = await client.get<{ guides: DocumentationGuide[]; total: number }>(
        '/docs/guides',
        { params }
      );
      return data;
    },
  });
}

export function useGuide(slug: string) {
  return useQuery({
    queryKey: ['guide', slug],
    queryFn: async () => {
      const { data } = await client.get<DocumentationGuide>(`/docs/guides/${slug}`);
      return data;
    },
    enabled: !!slug,
  });
}

export function useExamples(filters?: { category?: string; agent_id?: string; tag?: string }) {
  return useQuery({
    queryKey: ['examples', filters],
    queryFn: async () => {
      const { data } = await client.get<{ examples: DocumentationExample[]; total: number }>(
        '/docs/examples',
        { params: filters }
      );
      return data;
    },
  });
}

export function useExample(exampleId: string) {
  return useQuery({
    queryKey: ['example', exampleId],
    queryFn: async () => {
      const { data } = await client.get<DocumentationExample>(`/docs/examples/${exampleId}`);
      return data;
    },
    enabled: !!exampleId,
  });
}

export function useAgentDocumentation(agentId: string) {
  return useQuery({
    queryKey: ['agent-doc', agentId],
    queryFn: async () => {
      const { data } = await client.get<AgentDocumentation>(`/docs/agents/${agentId}`);
      return data;
    },
    enabled: !!agentId,
  });
}

export function useAllAgentDocs() {
  return useQuery({
    queryKey: ['agent-docs'],
    queryFn: async () => {
      const { data } = await client.get<{ agents: AgentDocumentation[]; total: number }>(
        '/docs/agents'
      );
      return data;
    },
  });
}
