export type Incident={id:string;title:string;order_id:string;state:string;severity:string;amount:string;mode:string;checked_at:string};
export type Event={id:string;source:string;event_type:string;payload:unknown;observed_at:string};
export type Report={summary:string;payment_truth:string;confirmed_facts:{claim:string;evidence_ids:string[]}[];unknowns:string[];conflicts:string[];recommended_next_steps:{action:string;requires_review:boolean;evidence_ids:string[]}[];support_reply_draft:string;validator_flags:string[];ai_status:string};
export type Detail={id:string;incident_id:string;title:string;state:string;amount:string;currency:string;mode:string;capture_id:string|null;events:Event[];investigation:Report|null};
export type Run={id:string;scenario?:string;passed:boolean;mode:string;assertions:{name:string;expected:unknown;actual:unknown;passed:boolean}[];trace:Event[]};
