BEGIN;
ALTER TABLE check_results ADD COLUMN scheduled_period INTEGER;
ALTER TABLE check_results
    ADD CONSTRAINT uq_check_results_monitor_period
    UNIQUE (monitor_id, scheduled_period);
COMMIT;
