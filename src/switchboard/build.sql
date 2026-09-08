-- timetable reference schema
CREATE TABLE toc_refs (
    toc CHAR(2) PRIMARY KEY,
    toc_name TEXT NOT NULL,
    url TEXT
);
CREATE TABLE location_refs (
    tiploc VARCHAR(7) PRIMARY KEY,
    crs CHAR(3),
    toc CHAR(2),
    location_name TEXT NOT NULL
);

CREATE INDEX idx_location_refs_crs ON location_refs(crs);

CREATE TABLE cancellation_reasons (
    reason_code TEXT PRIMARY KEY,
    reason_text TEXT NOT NULL
);

CREATE TABLE late_running_reasons (
    reason_code TEXT PRIMARY KEY,
    reason_text TEXT NOT NULL
);

CREATE TABLE via_points (
    at CHAR(3) NOT NULL,
    destination VARCHAR(7) NOT NULL REFERENCES location_refs(tiploc),
    loc1 VARCHAR(7) NOT NULL REFERENCES location_refs(tiploc),
    loc2 VARCHAR(7) REFERENCES location_refs(tiploc),
    via_text TEXT NOT NULL,
    CONSTRAINT uq_via_points UNIQUE NULLS NOT DISTINCT (at, destination, loc1, loc2)
);

CREATE INDEX idx_via_points_lookup ON via_points(at, destination);

CREATE TABLE cis_sources (
    code CHAR(4) PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE loading_categories (
    code VARCHAR(4) NOT NULL,
    name TEXT NOT NULL,
    toc CHAR(2) REFERENCES toc_refs(toc),
    typical_description TEXT NOT NULL,
    expected_description TEXT NOT NULL,
    definition TEXT NOT NULL,
    colour VARCHAR(10) NOT NULL,
    image_file TEXT NOT NULL,
    CONSTRAINT uq_loading_categories UNIQUE NULLS NOT DISTINCT (code, toc)
);




-- timetable static schema

CREATE TABLE schedules (
    rid VARCHAR(16) PRIMARY KEY,
    uid VARCHAR(6) NOT NULL,
    train_id VARCHAR(4) NOT NULL,
    ssd DATE NOT NULL,
    toc CHAR(2) NOT NULL,
    status VARCHAR(2) DEFAULT 'P',
    train_cat VARCHAR(2) DEFAULT 'OO',
    is_passenger_svc BOOLEAN DEFAULT TRUE,
    deleted BOOLEAN DEFAULT FALSE,
    is_charter BOOLEAN DEFAULT FALSE,
    qtrain BOOLEAN DEFAULT FALSE,
    can BOOLEAN DEFAULT FALSE,
    cancel_reason_code TEXT REFERENCES cancellation_reasons(reason_code),

    rsid TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    late_reason_code TEXT REFERENCES late_running_reasons(reason_code),
    diverted_via VARCHAR(7) REFERENCES location_refs(tiploc),
    diversion_reason_code TEXT,
    diversion_reason_tiploc VARCHAR(7) REFERENCES location_refs(tiploc),
    diversion_reason_near BOOLEAN
);

CREATE INDEX idx_schedules_uid_ssd ON schedules(uid, ssd);

CREATE TABLE schedule_locations (
    id BIGSERIAL PRIMARY KEY,
    rid VARCHAR(16) NOT NULL REFERENCES schedules(rid) ON DELETE CASCADE,
    loc_type VARCHAR(4) NOT NULL,
    tpl VARCHAR(7) NOT NULL REFERENCES location_refs(tiploc),
    act VARCHAR(12) DEFAULT '  ',
    plan_act VARCHAR(12),
    can BOOLEAN DEFAULT FALSE,
    plat VARCHAR(6),
    wta TIME,
    wtd TIME,
    wtp TIME,
    pta TIME,
    ptd TIME,
    fd VARCHAR(7) REFERENCES location_refs(tiploc),
    rdelay INT DEFAULT 0,
    seq INT NOT NULL,

    fid TEXT,
    avg_loading INT,
    cancel_reason_code TEXT REFERENCES cancellation_reasons(reason_code),
    affected_by_diversion BOOLEAN DEFAULT FALSE,

    CONSTRAINT uq_schedule_locations_rid_seq UNIQUE (rid, seq)
);
CREATE INDEX idx_schedule_locations_rid ON schedule_locations(rid);
CREATE INDEX idx_schedule_locations_tpl ON schedule_locations(tpl);

CREATE TABLE associations (
    id BIGSERIAL PRIMARY KEY,
    main_rid VARCHAR(16) NOT NULL,
    assoc_rid VARCHAR(16) NOT NULL,
    tiploc VARCHAR(7) NOT NULL REFERENCES location_refs(tiploc),
    category CHAR(2) NOT NULL, -- JJ, VV, LK, NP
    is_cancelled BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    main_wta TIME,
    main_wtd TIME,
    main_wtp TIME,
    main_pta TIME,
    main_ptd TIME,
    assoc_wta TIME,
    assoc_wtd TIME,
    assoc_wtp TIME,
    assoc_pta TIME,
    assoc_ptd TIME,
    CONSTRAINT uq_associations UNIQUE NULLS NOT DISTINCT (main_rid, assoc_rid, category, tiploc)
);

CREATE INDEX idx_associations_main_rid ON associations(main_rid);
CREATE INDEX idx_associations_assoc_rid ON associations(assoc_rid);
CREATE INDEX idx_associations_main_rid_lookup ON associations(main_rid);
CREATE INDEX idx_associations_assoc_rid_lookup ON associations(assoc_rid);




-- darwin push port
CREATE TABLE station_messages (
    station_message_id TEXT PRIMARY KEY,
    msg TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('0', '1', '2', '3', '4')),
    suppress BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE station_messages_locations (
    station_message_id TEXT REFERENCES station_messages(station_message_id) ON DELETE CASCADE,
    crs TEXT NOT NULL,
    PRIMARY KEY (station_message_id, crs)
);

CREATE TABLE system_status_logs (
    status_timestamp TIMESTAMP PRIMARY KEY,
    status_code TEXT NOT NULL,
    status_message TEXT NOT NULL
);

CREATE INDEX idx_station_messages_locations_crs ON station_messages_locations(crs);

CREATE TABLE ts_locations (
    id BIGSERIAL PRIMARY KEY,
    rid VARCHAR(16) NOT NULL,
    tpl VARCHAR(7) NOT NULL REFERENCES location_refs(tiploc),
    wta TIME,
    wtd TIME,
    wtp TIME,
    pta TIME,
    ptd TIME,

    arr_at TIME,
    arr_et TIME,
    arr_wet TIME,
    arr_src TEXT,
    arr_src_inst TEXT,
    arr_at_class TEXT,
    arr_at_removed BOOLEAN DEFAULT FALSE,
    arr_delayed BOOLEAN DEFAULT FALSE,
    arr_uncertainty TEXT,

    dep_at TIME,
    dep_et TIME,
    dep_wet TIME,
    dep_etmin TIME,
    dep_src TEXT,
    dep_src_inst TEXT,
    dep_at_class TEXT,
    dep_at_removed BOOLEAN DEFAULT FALSE,
    dep_delayed BOOLEAN DEFAULT FALSE,
    dep_uncertainty TEXT,

    pass_at TIME,
    pass_et TIME,
    pass_wet TIME,
    pass_src TEXT,
    pass_src_inst TEXT,
    pass_at_class TEXT,
    pass_at_removed BOOLEAN DEFAULT FALSE,
    pass_delayed BOOLEAN DEFAULT FALSE,
    pass_uncertainty TEXT,

    plat TEXT,
    plat_src TEXT,
    plat_conf BOOLEAN DEFAULT FALSE,
    plat_sup BOOLEAN DEFAULT FALSE,
    plat_cis_sup BOOLEAN DEFAULT FALSE,

    suppr BOOLEAN DEFAULT FALSE,
    length INT,
    detach_front BOOLEAN,
    divide_reverse_formation BOOLEAN,

    CONSTRAINT uq_ts_locations UNIQUE NULLS NOT DISTINCT (rid, tpl, wta, wtd, wtp)
);
CREATE INDEX idx_ts_locations_rid ON ts_locations(rid);
CREATE INDEX idx_ts_locations_tpl ON ts_locations(tpl);


CREATE TABLE train_formations (
    fid TEXT PRIMARY KEY,
    rid VARCHAR(16) NOT NULL,
    src TEXT,
    src_inst TEXT
);
CREATE INDEX idx_train_formations_rid ON train_formations(rid);

CREATE TABLE formation_coaches (
    id BIGSERIAL PRIMARY KEY,
    fid TEXT NOT NULL REFERENCES train_formations(fid) ON DELETE CASCADE,
    coach_number TEXT NOT NULL,
    coach_class TEXT,
    toilet_availability TEXT DEFAULT 'Unknown',
    toilet_status TEXT DEFAULT 'Unknown',
    seq INT NOT NULL,
    CONSTRAINT uq_formation_coaches UNIQUE (fid, coach_number)
);


CREATE TABLE formation_loading (
    id BIGSERIAL PRIMARY KEY,
    fid TEXT NOT NULL,
    rid VARCHAR(16) NOT NULL,
    tpl VARCHAR(7) NOT NULL REFERENCES location_refs(tiploc),
    wta TIME,
    wtd TIME,
    wtp TIME,
    pta TIME,
    ptd TIME,
    CONSTRAINT uq_formation_loading UNIQUE NULLS NOT DISTINCT (rid, tpl, wta, wtd, wtp)
);
CREATE INDEX idx_formation_loading_rid ON formation_loading(rid);
CREATE INDEX idx_formation_loading_fid ON formation_loading(fid);

CREATE TABLE formation_loading_coaches (
    id BIGSERIAL PRIMARY KEY,
    formation_loading_id BIGINT NOT NULL REFERENCES formation_loading(id) ON DELETE CASCADE,
    coach_number TEXT NOT NULL,
    src TEXT,
    src_inst TEXT,
    loading_value INT,
    CONSTRAINT uq_formation_loading_coaches UNIQUE (formation_loading_id, coach_number)
);


CREATE TABLE service_loading (
    id BIGSERIAL PRIMARY KEY,
    rid VARCHAR(16) NOT NULL,
    tpl VARCHAR(7) NOT NULL REFERENCES location_refs(tiploc),
    wta TIME,
    wtd TIME,
    wtp TIME,
    pta TIME,
    ptd TIME,
    loading_category TEXT,
    loading_category_src TEXT,
    loading_category_src_inst TEXT,
    loading_percentage INT,
    loading_percentage_src TEXT,
    loading_percentage_src_inst TEXT,
    CONSTRAINT uq_service_loading UNIQUE NULLS NOT DISTINCT (rid, tpl, wta, wtd, wtp)
);
CREATE INDEX idx_service_loading_rid ON service_loading(rid);


CREATE TABLE train_order (
    id BIGSERIAL PRIMARY KEY,
    tiploc VARCHAR(7) NOT NULL,
    crs CHAR(3) NOT NULL,
    CONSTRAINT uq_train_order_platform UNIQUE (tiploc, crs)
);

CREATE TABLE train_order_entries (
    id BIGSERIAL PRIMARY KEY,
    train_order_id BIGINT NOT NULL REFERENCES train_order(id) ON DELETE CASCADE,
    order_rank INT NOT NULL,
    rid VARCHAR(16),
    train_id VARCHAR(4),
    wta TIME,
    wtd TIME,
    wtp TIME,
    pta TIME,
    ptd TIME,
    CONSTRAINT uq_train_order_entries UNIQUE (train_order_id, order_rank)
);


CREATE TABLE train_alerts (
    alert_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    alert_text TEXT NOT NULL,
    audience TEXT,
    alert_type TEXT,
    send_by_sms BOOLEAN DEFAULT FALSE,
    send_by_email BOOLEAN DEFAULT FALSE,
    send_by_twitter BOOLEAN DEFAULT FALSE,
    copied_from_alert_id TEXT,
    copied_from_source TEXT
);

CREATE TABLE train_alert_services (
    id BIGSERIAL PRIMARY KEY,
    alert_id TEXT NOT NULL REFERENCES train_alerts(alert_id) ON DELETE CASCADE,
    uid VARCHAR(6),
    ssd DATE
);
CREATE INDEX idx_train_alert_services_alert_id ON train_alert_services(alert_id);

CREATE TABLE train_alert_locations (
    id BIGSERIAL PRIMARY KEY,
    alert_service_id BIGINT NOT NULL REFERENCES train_alert_services(id) ON DELETE CASCADE,
    crs CHAR(3) NOT NULL,
    seq INT NOT NULL
);


CREATE TABLE tracking_id_corrections (
    id BIGSERIAL PRIMARY KEY,
    berth TEXT NOT NULL,
    td_area TEXT,
    incorrect_tracking_id TEXT,
    correct_tracking_id TEXT NOT NULL,
    corrected_at TIMESTAMP NOT NULL DEFAULT now()
);


CREATE TABLE alarms (
    alarm_id TEXT PRIMARY KEY,
    alarm_type TEXT NOT NULL,
    td_area TEXT,
    is_cleared BOOLEAN NOT NULL DEFAULT FALSE,
    raised_at TIMESTAMP NOT NULL DEFAULT now(),
    cleared_at TIMESTAMP
);


-- prep for v19
CREATE TABLE station_lift_status (
    id BIGSERIAL PRIMARY KEY,
    crs CHAR(3) NOT NULL,
    lift_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OutOfService',
    description TEXT,
    CONSTRAINT uq_station_lift_status UNIQUE (crs, lift_id)
);
CREATE INDEX idx_station_lift_status_crs ON station_lift_status(crs);