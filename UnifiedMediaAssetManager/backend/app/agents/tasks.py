"""
Celery tasks for AI agent job processing.

This module defines async tasks for processing agent jobs through the Celery
distributed task queue.
"""
import logging
from datetime import datetime
from typing import Dict, Any

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.database import AgentJobDB
from .narrative_agent import NarrativeAgent
from .spatial_agent import SpatialAgent
from .consistency_agent import ConsistencyAgent

logger = logging.getLogger(__name__)

# Agent type mapping
AGENT_CLASSES = {
    'narrative': NarrativeAgent,
    'spatial': SpatialAgent,
    'consistency': ConsistencyAgent,
}


@celery_app.task(bind=True, max_retries=3)
def process_agent_job(self, job_id: str) -> Dict[str, Any]:
    """
    Process an AI agent job asynchronously.

    This task:
    1. Loads the job from the database
    2. Instantiates the appropriate agent
    3. Processes the job
    4. Updates the database with results
    5. Handles retries on failure

    Args:
        job_id: UUID of the agent job to process

    Returns:
        Dictionary containing job results

    Raises:
        Exception: If job fails after all retries
    """
    db = SessionLocal()

    try:
        # Load the job from database
        job = db.query(AgentJobDB).filter(AgentJobDB.id == job_id).first()

        if not job:
            logger.error(f"Job {job_id} not found in database")
            raise ValueError(f"Job {job_id} not found")

        # Validate agent type
        if job.agent_type not in AGENT_CLASSES:
            logger.error(f"Unknown agent type: {job.agent_type}")
            job.status = 'failed'
            job.error_message = f"Unknown agent type: {job.agent_type}"
            job.completed_at = datetime.utcnow()
            db.commit()
            return {'success': False, 'error': job.error_message}

        # Update job status to processing
        job.status = 'processing'
        job.started_at = datetime.utcnow()
        db.commit()

        logger.info(f"Processing job {job_id} with agent type: {job.agent_type}")

        # Instantiate the appropriate agent
        agent_class = AGENT_CLASSES[job.agent_type]
        agent = agent_class()

        # Process the job (this is an async method, but we need to run it synchronously in Celery)
        import asyncio

        # Create a new event loop for this task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(agent.execute(job_id, job.input_data))
        finally:
            loop.close()

        # Update job with results
        if result['success']:
            job.status = 'completed'
            job.output_data = result['output_data']
            job.confidence_score = result['confidence_score']
            job.human_review_required = result['human_review_required']
            job.error_message = None

            logger.info(
                f"Job {job_id} completed successfully. "
                f"Confidence: {result['confidence_score']:.2f}, "
                f"Review required: {result['human_review_required']}"
            )
        else:
            job.status = 'failed'
            job.error_message = result.get('error', 'Unknown error')
            job.human_review_required = True

            logger.error(f"Job {job_id} failed: {job.error_message}")

            # Retry on failure
            if self.request.retries < self.max_retries:
                logger.info(f"Retrying job {job_id} (attempt {self.request.retries + 1}/{self.max_retries})")
                # Reset status for retry
                job.status = 'pending'
                db.commit()
                # Retry with exponential backoff
                raise self.retry(exc=Exception(job.error_message), countdown=2 ** self.request.retries)

        job.completed_at = datetime.utcnow()
        db.commit()

        return {
            'success': result['success'],
            'job_id': job_id,
            'agent_type': job.agent_type,
            'status': job.status,
            'confidence_score': job.confidence_score,
            'human_review_required': job.human_review_required
        }

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}", exc_info=True)

        # Update job status in database
        try:
            job = db.query(AgentJobDB).filter(AgentJobDB.id == job_id).first()
            if job:
                job.status = 'failed'
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                job.human_review_required = True
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update job status in database: {str(db_error)}")

        # Retry if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=2 ** self.request.retries)

        # If we've exhausted retries, raise the exception
        raise

    finally:
        db.close()


@celery_app.task
def cleanup_old_jobs(days: int = 30) -> Dict[str, Any]:
    """
    Clean up old completed jobs from the database.

    This task should be run periodically (e.g., daily) to prevent
    the agent_jobs table from growing indefinitely.

    Args:
        days: Delete jobs older than this many days

    Returns:
        Dictionary with cleanup statistics
    """
    db = SessionLocal()

    try:
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Count jobs to be deleted
        jobs_to_delete = db.query(AgentJobDB).filter(
            AgentJobDB.completed_at < cutoff_date,
            AgentJobDB.status.in_(['completed', 'failed'])
        ).count()

        # Delete old jobs
        deleted = db.query(AgentJobDB).filter(
            AgentJobDB.completed_at < cutoff_date,
            AgentJobDB.status.in_(['completed', 'failed'])
        ).delete(synchronize_session=False)

        db.commit()

        logger.info(f"Cleaned up {deleted} old agent jobs (older than {days} days)")

        return {
            'success': True,
            'deleted_count': deleted,
            'cutoff_date': cutoff_date.isoformat()
        }

    except Exception as e:
        logger.error(f"Error cleaning up old jobs: {str(e)}", exc_info=True)
        db.rollback()
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        db.close()


@celery_app.task
def get_job_stats() -> Dict[str, Any]:
    """
    Get statistics about agent jobs.

    Returns:
        Dictionary with job statistics by status and agent type
    """
    db = SessionLocal()

    try:
        from sqlalchemy import func

        # Get counts by status
        status_counts = db.query(
            AgentJobDB.status,
            func.count(AgentJobDB.id)
        ).group_by(AgentJobDB.status).all()

        # Get counts by agent type
        agent_type_counts = db.query(
            AgentJobDB.agent_type,
            func.count(AgentJobDB.id)
        ).group_by(AgentJobDB.agent_type).all()

        # Get average confidence scores by agent type
        avg_confidence = db.query(
            AgentJobDB.agent_type,
            func.avg(AgentJobDB.confidence_score)
        ).filter(
            AgentJobDB.confidence_score.isnot(None)
        ).group_by(AgentJobDB.agent_type).all()

        # Get human review stats
        review_required_count = db.query(AgentJobDB).filter(
            AgentJobDB.human_review_required == True
        ).count()

        return {
            'status_counts': {status: count for status, count in status_counts},
            'agent_type_counts': {agent_type: count for agent_type, count in agent_type_counts},
            'avg_confidence_by_type': {agent_type: float(avg) for agent_type, avg in avg_confidence},
            'human_review_required': review_required_count,
            'total_jobs': db.query(AgentJobDB).count()
        }

    except Exception as e:
        logger.error(f"Error getting job stats: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        db.close()
