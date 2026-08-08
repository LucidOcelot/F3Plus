#include <stdint.h>
#include "generator.h"
#include "finders.h"

/* F3+'s intentionally tiny ABI over upstream Cubiomes.
   This file is F3+ code; Cubiomes remains separately MIT-licensed. */

int minescript_cubiomes_newest(void) {
    return MC_NEWEST;
}

int minescript_cubiomes_biome_at(int64_t seed, int mc, int dim, int x, int y, int z) {
    Generator g;
    if (mc <= 0) mc = MC_NEWEST;
    setupGenerator(&g, mc, 0);
    applySeed(&g, dim, (uint64_t)seed);
    return getBiomeAt(&g, 1, x, y, z);
}

int minescript_cubiomes_structure_config(int structure_type, int mc,
        int *salt, int *region_size, int *chunk_range, int *dim) {
    StructureConfig c;
    if (mc <= 0) mc = MC_NEWEST;
    if (!getStructureConfig(structure_type, mc, &c)) return 0;
    if (salt) *salt = c.salt;
    if (region_size) *region_size = c.regionSize;
    if (chunk_range) *chunk_range = c.chunkRange;
    if (dim) *dim = c.dim;
    return 1;
}

int minescript_cubiomes_structure_pos(int64_t seed, int mc, int structure_type,
        int region_x, int region_z, int *chunk_x, int *chunk_z) {
    Pos p;
    if (mc <= 0) mc = MC_NEWEST;
    if (!getStructurePos(structure_type, mc, (uint64_t)seed, region_x, region_z, &p)) return 0;
    if (chunk_x) *chunk_x = p.x >> 4;
    if (chunk_z) *chunk_z = p.z >> 4;
    return 1;
}
