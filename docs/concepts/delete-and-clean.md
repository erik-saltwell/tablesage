# Delete and Clean Up

TableSage separates removing an object from removing its files. **Delete**
removes the object's record from TableSage's database, but intentionally leaves
its folder on disk. **Clean Up** later removes folders that no longer belong to
an object in the database.

This separation protects recordings and generated material from an accidental,
irreversible removal. After deleting an object, its files remain available for
inspection, backup, or manual recovery until the user explicitly confirms a
cleanup. Clean Up is the point at which those orphaned folders are permanently
removed.

## Objects that use this lifecycle

The delete-then-clean-up lifecycle applies to the directory-backed objects:

- **Players.** Deleting an unused Player removes its workspace record and
  leaves the Player's folder, including voice samples, until player cleanup.
  A Player who has attended a Session cannot be deleted until that attendance
  is removed.
- **Campaigns.** Deleting a Campaign removes its database record and leaves
  its campaign folder until campaign cleanup. That folder can include the
  folders and material for its Sessions.
- **Sessions.** Deleting a Session removes its database record, including its
  attendance and session-scoped roles, and leaves its numbered Session folder
  until cleanup for that Campaign.

Clean Up identifies these remaining folders by comparing the folders on disk
with the current database records. It removes only folders with no matching
Player, Campaign, or Session record.

## Related actions

This lifecycle does not make every destructive action a two-step operation.
Deleting an individual voice sample or an individual session artifact removes
that file directly. **Clean Session** is also different: it keeps the Session
record but deletes all of that Session's artifacts, including its input audio.
Those actions have their own confirmations where appropriate.
