SELECT u.name
FROM registrations r
JOIN users u ON r.user_id = u.id
WHERE r.event_id = :event_id
ORDER BY u.name;