/**
 * FlipFlow Scout Agent - Job Queue
 * Simple in-memory job queue for scraping and analysis tasks
 */

export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
export type JobType = 'scrape' | 'analyze' | 'alert' | 'cleanup';

export interface Job<T = any> {
  id: string;
  type: JobType;
  status: JobStatus;
  data: T;
  result?: any;
  error?: string;
  attempts: number;
  maxAttempts: number;
  createdAt: Date;
  startedAt?: Date;
  completedAt?: Date;
  scheduledFor?: Date;
  priority: number; // Higher = more important
  metadata?: Record<string, any>;
}

export interface ScrapeJobData {
  options?: any;
  filters?: any;
  source: 'manual' | 'scheduled' | 'api' | 'webhook';
  userId?: string;
  notifyOnComplete?: boolean;
}

export interface AnalyzeJobData {
  listingId: string;
  listingUrl?: string;
  listingData?: string;
  userId?: string;
  notifyOnComplete?: boolean;
}

export interface AlertJobData {
  userId: string;
  alertId: string;
  listings: string[];
  minScore?: number;
}

export interface JobQueueConfig {
  maxConcurrent: number;
  maxRetries: number;
  retryDelay: number;
  jobTimeout: number;
  cleanupInterval: number;
  maxQueueSize: number;
}

export const DEFAULT_QUEUE_CONFIG: JobQueueConfig = {
  maxConcurrent: 3,
  maxRetries: 3,
  retryDelay: 5000,
  jobTimeout: 300000, // 5 minutes
  cleanupInterval: 3600000, // 1 hour
  maxQueueSize: 1000,
};

export class JobQueue {
  private jobs: Map<string, Job> = new Map();
  private processing: Set<string> = new Set();
  private config: JobQueueConfig;
  private cleanupTimer?: NodeJS.Timeout;
  private listeners: Map<string, Set<(job: Job) => void>> = new Map();

  constructor(config?: Partial<JobQueueConfig>) {
    this.config = { ...DEFAULT_QUEUE_CONFIG, ...config };
    this.startCleanup();
  }

  /**
   * Add a new job to the queue
   */
  add<T = any>(
    type: JobType,
    data: T,
    options?: {
      priority?: number;
      maxAttempts?: number;
      scheduledFor?: Date;
      metadata?: Record<string, any>;
    }
  ): Job<T> {
    // Check queue size
    if (this.jobs.size >= this.config.maxQueueSize) {
      throw new Error('Queue is full');
    }

    const job: Job<T> = {
      id: this.generateJobId(),
      type,
      status: 'pending',
      data,
      attempts: 0,
      maxAttempts: options?.maxAttempts || this.config.maxRetries,
      createdAt: new Date(),
      scheduledFor: options?.scheduledFor,
      priority: options?.priority || 0,
      metadata: options?.metadata,
    };

    this.jobs.set(job.id, job);
    this.emit('added', job);

    console.log(`Job ${job.id} (${job.type}) added to queue`);

    // Start processing if not at max concurrent
    this.processNext();

    return job;
  }

  /**
   * Process next job in queue
   */
  private async processNext(): Promise<void> {
    // Check if we can process more jobs
    if (this.processing.size >= this.config.maxConcurrent) {
      return;
    }

    // Find next job to process
    const job = this.getNextJob();
    if (!job) {
      return;
    }

    // Mark as processing
    this.processing.add(job.id);
    job.status = 'processing';
    job.startedAt = new Date();
    job.attempts++;

    this.emit('started', job);
    console.log(`Processing job ${job.id} (${job.type}), attempt ${job.attempts}/${job.maxAttempts}`);

    try {
      // Set timeout
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Job timeout')), this.config.jobTimeout);
      });

      // Process job with timeout
      const result = await Promise.race([
        this.processJob(job),
        timeoutPromise,
      ]);

      // Job completed successfully
      job.status = 'completed';
      job.completedAt = new Date();
      job.result = result;

      this.emit('completed', job);
      console.log(`Job ${job.id} completed successfully`);
    } catch (error) {
      // Job failed
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error(`Job ${job.id} failed:`, errorMessage);

      // Check if we should retry
      if (job.attempts < job.maxAttempts) {
        // Retry
        job.status = 'pending';
        job.scheduledFor = new Date(Date.now() + this.config.retryDelay);
        this.emit('retrying', job);
        console.log(`Job ${job.id} will be retried (attempt ${job.attempts + 1}/${job.maxAttempts})`);
      } else {
        // Max attempts reached
        job.status = 'failed';
        job.completedAt = new Date();
        job.error = errorMessage;
        this.emit('failed', job);
        console.error(`Job ${job.id} failed permanently after ${job.attempts} attempts`);
      }
    } finally {
      this.processing.delete(job.id);

      // Process next job
      setTimeout(() => this.processNext(), 100);
    }
  }

  /**
   * Get next job to process (by priority and scheduled time)
   */
  private getNextJob(): Job | null {
    const now = new Date();
    let bestJob: Job | null = null;
    let bestScore = -Infinity;

    for (const job of this.jobs.values()) {
      // Skip if not pending or scheduled for future
      if (job.status !== 'pending') continue;
      if (job.scheduledFor && job.scheduledFor > now) continue;

      // Calculate job score (higher = better)
      const score = job.priority * 1000 - job.createdAt.getTime();

      if (score > bestScore) {
        bestScore = score;
        bestJob = job;
      }
    }

    return bestJob;
  }

  /**
   * Process a job based on its type
   */
  private async processJob(job: Job): Promise<any> {
    switch (job.type) {
      case 'scrape':
        return this.processScrapeJob(job as Job<ScrapeJobData>);
      case 'analyze':
        return this.processAnalyzeJob(job as Job<AnalyzeJobData>);
      case 'alert':
        return this.processAlertJob(job as Job<AlertJobData>);
      case 'cleanup':
        return this.processCleanupJob(job);
      default:
        throw new Error(`Unknown job type: ${job.type}`);
    }
  }

  /**
   * Process scrape job
   */
  private async processScrapeJob(job: Job<ScrapeJobData>): Promise<any> {
    // Import scraper dynamically to avoid circular dependencies
    const { getScraperInstance } = await import('./scraper/flippa-scraper');

    const scraper = getScraperInstance();
    const result = await scraper.scrapeListings(job.data.options);

    // Store listings in database
    if (result.success && result.listings.length > 0) {
      await this.storeListings(result.listings);
    }

    return {
      success: result.success,
      listingsFound: result.listings.length,
      pagesScraped: result.metadata.pagesScraped,
      duration: result.metadata.duration,
    };
  }

  /**
   * Process analyze job
   */
  private async processAnalyzeJob(job: Job<AnalyzeJobData>): Promise<any> {
    const { analyzeFlippaListing } = await import('./analyzer');

    const analysis = await analyzeFlippaListing(
      job.data.listingData || '',
      job.data.listingUrl
    );

    // Store analysis in database
    await this.storeAnalysis(job.data.listingId, analysis);

    return analysis;
  }

  /**
   * Process alert job
   */
  private async processAlertJob(job: Job<AlertJobData>): Promise<any> {
    // Send alert to user (email, webhook, etc.)
    console.log(`Sending alert to user ${job.data.userId} for ${job.data.listings.length} listings`);

    // TODO: Implement email/webhook notification

    return {
      success: true,
      listingsAlerted: job.data.listings.length,
    };
  }

  /**
   * Process cleanup job
   */
  private async processCleanupJob(job: Job): Promise<any> {
    const removed = this.cleanup();
    return { removed };
  }

  /**
   * Store listings in database (placeholder)
   */
  private async storeListings(listings: any[]): Promise<void> {
    // TODO: Implement database storage
    console.log(`Storing ${listings.length} listings in database`);
  }

  /**
   * Store analysis in database (placeholder)
   */
  private async storeAnalysis(listingId: string, analysis: any): Promise<void> {
    // TODO: Implement database storage
    console.log(`Storing analysis for listing ${listingId}`);
  }

  /**
   * Get job by ID
   */
  get(id: string): Job | null {
    return this.jobs.get(id) || null;
  }

  /**
   * Get all jobs matching filter
   */
  getAll(filter?: {
    type?: JobType;
    status?: JobStatus;
    userId?: string;
  }): Job[] {
    const jobs = Array.from(this.jobs.values());

    if (!filter) return jobs;

    return jobs.filter((job) => {
      if (filter.type && job.type !== filter.type) return false;
      if (filter.status && job.status !== filter.status) return false;
      if (filter.userId && job.metadata?.userId !== filter.userId) return false;
      return true;
    });
  }

  /**
   * Cancel a job
   */
  cancel(id: string): boolean {
    const job = this.jobs.get(id);
    if (!job) return false;

    if (job.status === 'processing') {
      console.warn(`Cannot cancel job ${id} while processing`);
      return false;
    }

    job.status = 'cancelled';
    job.completedAt = new Date();
    this.emit('cancelled', job);

    return true;
  }

  /**
   * Remove a job from queue
   */
  remove(id: string): boolean {
    const job = this.jobs.get(id);
    if (!job) return false;

    if (job.status === 'processing') {
      console.warn(`Cannot remove job ${id} while processing`);
      return false;
    }

    this.jobs.delete(id);
    this.emit('removed', job);

    return true;
  }

  /**
   * Clean up old completed/failed jobs
   */
  cleanup(maxAge: number = 86400000): number {
    const now = Date.now();
    let removed = 0;

    for (const [id, job] of this.jobs.entries()) {
      if (
        (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') &&
        job.completedAt &&
        now - job.completedAt.getTime() > maxAge
      ) {
        this.jobs.delete(id);
        removed++;
      }
    }

    if (removed > 0) {
      console.log(`Cleaned up ${removed} old jobs`);
    }

    return removed;
  }

  /**
   * Start automatic cleanup
   */
  private startCleanup(): void {
    this.cleanupTimer = setInterval(() => {
      this.cleanup();
    }, this.config.cleanupInterval);
  }

  /**
   * Stop automatic cleanup
   */
  stopCleanup(): void {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = undefined;
    }
  }

  /**
   * Get queue statistics
   */
  getStats() {
    const jobs = Array.from(this.jobs.values());

    return {
      total: jobs.length,
      pending: jobs.filter((j) => j.status === 'pending').length,
      processing: jobs.filter((j) => j.status === 'processing').length,
      completed: jobs.filter((j) => j.status === 'completed').length,
      failed: jobs.filter((j) => j.status === 'failed').length,
      cancelled: jobs.filter((j) => j.status === 'cancelled').length,
      byType: {
        scrape: jobs.filter((j) => j.type === 'scrape').length,
        analyze: jobs.filter((j) => j.type === 'analyze').length,
        alert: jobs.filter((j) => j.type === 'alert').length,
        cleanup: jobs.filter((j) => j.type === 'cleanup').length,
      },
    };
  }

  /**
   * Clear all jobs
   */
  clear(): void {
    this.jobs.clear();
    this.processing.clear();
    this.emit('cleared', null);
  }

  /**
   * Event listener management
   */
  on(event: string, callback: (job: Job) => void): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  off(event: string, callback: (job: Job) => void): void {
    const listeners = this.listeners.get(event);
    if (listeners) {
      listeners.delete(callback);
    }
  }

  private emit(event: string, job: Job | null): void {
    const listeners = this.listeners.get(event);
    if (listeners && job) {
      listeners.forEach((callback) => callback(job));
    }
  }

  /**
   * Generate unique job ID
   */
  private generateJobId(): string {
    return `job_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  }

  /**
   * Shutdown queue gracefully
   */
  async shutdown(): Promise<void> {
    console.log('Shutting down job queue...');
    this.stopCleanup();

    // Wait for processing jobs to complete (with timeout)
    const timeout = 30000; // 30 seconds
    const start = Date.now();

    while (this.processing.size > 0 && Date.now() - start < timeout) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }

    if (this.processing.size > 0) {
      console.warn(`${this.processing.size} jobs still processing after timeout`);
    }

    console.log('Job queue shut down');
  }
}

// Singleton instance
let queueInstance: JobQueue | null = null;

export function getQueueInstance(config?: Partial<JobQueueConfig>): JobQueue {
  if (!queueInstance) {
    queueInstance = new JobQueue(config);
  }
  return queueInstance;
}

export async function shutdownQueue(): Promise<void> {
  if (queueInstance) {
    await queueInstance.shutdown();
    queueInstance = null;
  }
}
