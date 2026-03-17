// PrepIQ MongoDB Initialisation
// Runs once on first container start
// Creates the event store database, collections, indexes, and TTL policies

const db = db.getSiblingDB('prepiq_events');

// ─── COLLECTION: user_events ──────────────────────────────────────────────────
// General user activity stream: logins, page views, module starts/completions
db.createCollection('user_events', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['user_id', 'event_type', 'timestamp'],
      properties: {
        user_id:    { bsonType: 'int',    description: 'PostgreSQL user ID' },
        event_type: { bsonType: 'string', description: 'e.g. login, module_start, module_complete, quiz_submit' },
        timestamp:  { bsonType: 'date' },
        metadata:   { bsonType: 'object', description: 'Flexible event-specific payload' },
        session_id: { bsonType: 'string' },
        ip_address: { bsonType: 'string' },
        user_agent: { bsonType: 'string' },
      }
    }
  }
});

db.user_events.createIndex({ user_id: 1, timestamp: -1 });
db.user_events.createIndex({ event_type: 1, timestamp: -1 });
db.user_events.createIndex({ timestamp: -1 });
// Auto-delete events older than 1 year
db.user_events.createIndex({ timestamp: 1 }, { expireAfterSeconds: 31536000 });

// ─── COLLECTION: simulation_traces ────────────────────────────────────────────
// Full step-by-step action traces for simulation sessions
// Variable schema per scenario — perfect for MongoDB
db.createCollection('simulation_traces', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['session_id', 'user_id', 'scenario_id', 'timestamp'],
      properties: {
        session_id:  { bsonType: 'int' },
        user_id:     { bsonType: 'int' },
        scenario_id: { bsonType: 'int' },
        step:        { bsonType: 'int' },
        action:      { bsonType: 'string' },
        is_correct:  { bsonType: 'bool' },
        hint_used:   { bsonType: 'bool' },
        time_taken_seconds: { bsonType: 'int' },
        timestamp:   { bsonType: 'date' },
        context:     { bsonType: 'object', description: 'Scenario-specific step context' },
      }
    }
  }
});

db.simulation_traces.createIndex({ session_id: 1 });
db.simulation_traces.createIndex({ user_id: 1, timestamp: -1 });
db.simulation_traces.createIndex({ scenario_id: 1, action: 1 });
// Retain simulation traces for 2 years
db.simulation_traces.createIndex({ timestamp: 1 }, { expireAfterSeconds: 63072000 });

// ─── COLLECTION: ai_coach_logs ────────────────────────────────────────────────
// AI Cyber Coach conversation turns for review and fine-tuning
db.createCollection('ai_coach_logs', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['user_id', 'timestamp', 'role', 'content'],
      properties: {
        user_id:        { bsonType: 'int' },
        session_ref:    { bsonType: 'string', description: 'Conversation thread ID' },
        role:           { bsonType: 'string', enum: ['user', 'assistant'] },
        content:        { bsonType: 'string' },
        context_module: { bsonType: 'string', description: 'Which module/scenario the user was in' },
        tokens_used:    { bsonType: 'int' },
        latency_ms:     { bsonType: 'int' },
        timestamp:      { bsonType: 'date' },
        flagged:        { bsonType: 'bool', description: 'Flagged for human review' },
      }
    }
  }
});

db.ai_coach_logs.createIndex({ user_id: 1, timestamp: -1 });
db.ai_coach_logs.createIndex({ session_ref: 1 });
db.ai_coach_logs.createIndex({ flagged: 1 });
// AI logs retained 90 days by default (GDPR consideration)
db.ai_coach_logs.createIndex({ timestamp: 1 }, { expireAfterSeconds: 7776000 });

// ─── COLLECTION: platform_metrics ─────────────────────────────────────────────
// Pre-aggregated daily/hourly metrics for the national dashboard
// Written by a scheduled job, read by the analytics API
db.createCollection('platform_metrics', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['period', 'period_start', 'metric_type'],
      properties: {
        period:        { bsonType: 'string', enum: ['hourly', 'daily', 'weekly'] },
        period_start:  { bsonType: 'date' },
        metric_type:   { bsonType: 'string', description: 'e.g. active_users, completions, avg_risk_score' },
        value:         { bsonType: 'double' },
        breakdown:     { bsonType: 'object', description: 'Optional by sector/region breakdown' },
        computed_at:   { bsonType: 'date' },
      }
    }
  }
});

db.platform_metrics.createIndex({ period: 1, period_start: -1, metric_type: 1 }, { unique: true });
db.platform_metrics.createIndex({ metric_type: 1, period_start: -1 });

// ─── COLLECTION: threat_intel_feed ────────────────────────────────────────────
// Stores scraped/imported threat intelligence items for content currency
db.createCollection('threat_intel_feed', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['title', 'source', 'published_at'],
      properties: {
        title:        { bsonType: 'string' },
        summary:      { bsonType: 'string' },
        source:       { bsonType: 'string' },
        url:          { bsonType: 'string' },
        tags:         { bsonType: 'array' },
        severity:     { bsonType: 'string', enum: ['info', 'low', 'medium', 'high', 'critical'] },
        sectors:      { bsonType: 'array', description: 'Relevant industry sectors' },
        published_at: { bsonType: 'date' },
        imported_at:  { bsonType: 'date' },
        is_featured:  { bsonType: 'bool' },
      }
    }
  }
});

db.threat_intel_feed.createIndex({ published_at: -1 });
db.threat_intel_feed.createIndex({ tags: 1 });
db.threat_intel_feed.createIndex({ severity: 1, published_at: -1 });
db.threat_intel_feed.createIndex({ is_featured: 1 });
// Auto-expire old threat intel after 6 months
db.threat_intel_feed.createIndex({ imported_at: 1 }, { expireAfterSeconds: 15552000 });

print('✓ PrepIQ MongoDB initialised');
print('  Collections: user_events, simulation_traces, ai_coach_logs, platform_metrics, threat_intel_feed');
print('  TTL indexes configured for GDPR-compliant data retention');
