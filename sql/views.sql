IF OBJECT_ID('dbo.vwQueueOpen', 'V') IS NOT NULL DROP VIEW dbo.vwQueueOpen;
GO

CREATE VIEW dbo.vwQueueOpen AS
SELECT
    q.QueueItemId,
    q.CreatedAt,
    q.QueueName,
    q.Status,
    q.Reason,
    i.IntakeId,
    i.DomainModule,
    i.Priority,
    i.Crisis
FROM dbo.QueueItem q
JOIN dbo.Intake i ON i.IntakeId = q.IntakeId
WHERE q.Status = 'Open';
GO
