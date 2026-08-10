# F3+ 2.4 regression restoration

This internal engineering note tracks the post-consolidation regression pass. It is not linked from user-facing documentation and can be removed after the restoration is fully verified.

Covered in this branch:
- automatic update installation restored by default with explicit check-only/skip overrides;
- until-found search distinguishes a backend/prerequisite failure from a completed search attempt;
- Minecraft-managed Java runtime discovery expanded on Windows;
- canonical operation dialogs restored as searchable full workspaces with in-place structured results;
- maps/charts reconnected to the production result path;
- operation-specific position/navigation fields prevent generic unused inputs;
- Villager Explorer uses a substantially broader explicitly labeled fallback reference and visual profession rail;
- loot-table namespace loading is cached in a single ZIP pass;
- rich loot table browser/simulator restored without the old runtime patch stack.
