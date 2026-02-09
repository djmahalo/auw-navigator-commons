-- Seed a couple of rules.
-- MatchJson uses the rules_engine match language.

DELETE FROM dbo.Rule;
GO

-- Housing crisis => HousingEscalation queue
INSERT INTO dbo.Rule (RuleName, IsEnabled, PriorityOrder, MatchJson, Action, ActionParamsJson)
VALUES
(
  'Housing Crisis Escalation',
  1,
  10,
  N'{"all":[
      {"field":"DomainModule","op":"eq","value":"Housing"},
      {"field":"Crisis","op":"eq","value":true}
  ]}',
  'set_queue',
  N'{"queue":"HousingEscalation","reason":"Client reports housing crisis and needs immediate assistance."}'
);

-- Narrative contains "eviction" and risk_days <= 7 => HousingEscalation
INSERT INTO dbo.Rule (RuleName, IsEnabled, PriorityOrder, MatchJson, Action, ActionParamsJson)
VALUES
(
  'Eviction Risk (<=7 days)',
  1,
  20,
  N'{"all":[
      {"field":"DomainModule","op":"eq","value":"Housing"},
      {"field":"Narrative","op":"contains","value":"eviction"},
      {"attr":"risk_days","op":"lte","value":7}
  ]}',
  'set_queue',
  N'{"queue":"HousingEscalation","reason":"Eviction risk within 7 days."}'
);
GO
