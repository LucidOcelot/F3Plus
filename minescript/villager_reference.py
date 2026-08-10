from __future__ import annotations

"""Comprehensive vanilla-style villager planning reference.

Installed trade JSON remains authoritative.  This module only expands the explicitly
non-exact fallback used when Minecraft does not expose usable trade definitions in an
installed JAR.  It represents possible standard profession/level offers so the explorer
is useful without claiming selected-snapshot exactness.
"""

from .villagers import Trade

REFERENCE_SOURCE = "Bundled comprehensive planning reference"


def _t(prof, level, name, wc, wid, gc, gid, uses=12, xp=1, *, add=None, detail=""):
    add_text = f"{add[0]} {add[1]}" if add else None
    return Trade(
        profession=prof, level=level, name=name,
        wants=f"{wc} {wid}", gives=f"{gc} {gid}", additional_wants=add_text,
        max_uses=uses, xp=xp, source="bundled-comprehensive-reference",
        raw_path=f"reference/{prof}/{level}/{name.replace(' ', '_')}",
        wants_id=wid, wants_count=str(wc),
        additional_wants_id=add[1] if add else "", additional_wants_count=str(add[0]) if add else "1",
        gives_id=gid, gives_count=str(gc), details=detail,
    )


def reference_trades() -> list[Trade]:
    t = _t
    rows = [
        # Armorer
        t("armorer",1,"coal for emerald",15,"coal",1,"emerald",16),
        t("armorer",1,"iron helmet",5,"emerald",1,"iron_helmet"), t("armorer",1,"iron chestplate",9,"emerald",1,"iron_chestplate"),
        t("armorer",1,"iron leggings",7,"emerald",1,"iron_leggings"), t("armorer",1,"iron boots",4,"emerald",1,"iron_boots"),
        t("armorer",2,"iron for emerald",4,"iron_ingot",1,"emerald",12), t("armorer",2,"bell",36,"emerald",1,"bell",12),
        t("armorer",3,"lava bucket for emerald",1,"lava_bucket",1,"emerald",12), t("armorer",3,"diamond for emerald",1,"diamond",1,"emerald",12),
        t("armorer",3,"chainmail helmet",1,"emerald",1,"chainmail_helmet"), t("armorer",3,"chainmail chestplate",4,"emerald",1,"chainmail_chestplate"),
        t("armorer",3,"chainmail leggings",3,"emerald",1,"chainmail_leggings"), t("armorer",3,"chainmail boots",1,"emerald",1,"chainmail_boots"),
        t("armorer",4,"enchanted diamond leggings",14,"emerald",1,"diamond_leggings",3,15,detail="Enchantments and final price vary by offer/version."),
        t("armorer",4,"enchanted diamond boots",8,"emerald",1,"diamond_boots",3,15,detail="Enchantments and final price vary by offer/version."),
        t("armorer",5,"enchanted diamond helmet",13,"emerald",1,"diamond_helmet",3,30,detail="Enchantments and final price vary by offer/version."),
        t("armorer",5,"enchanted diamond chestplate",21,"emerald",1,"diamond_chestplate",3,30,detail="Enchantments and final price vary by offer/version."),

        # Butcher
        t("butcher",1,"raw chicken for emerald",14,"chicken",1,"emerald",16), t("butcher",1,"raw rabbit for emerald",4,"rabbit",1,"emerald",16),
        t("butcher",1,"rabbit stew",1,"emerald",1,"rabbit_stew",12), t("butcher",2,"raw porkchop for emerald",7,"porkchop",1,"emerald",16),
        t("butcher",2,"raw mutton for emerald",4,"mutton",1,"emerald",16), t("butcher",3,"cooked porkchop",1,"emerald",5,"cooked_porkchop",16),
        t("butcher",3,"cooked chicken",1,"emerald",8,"cooked_chicken",16), t("butcher",4,"dried kelp block for emerald",10,"dried_kelp_block",1,"emerald",12),
        t("butcher",5,"sweet berries for emerald",10,"sweet_berries",1,"emerald",12),

        # Cartographer
        t("cartographer",1,"paper for emerald",24,"paper",1,"emerald",16), t("cartographer",1,"empty map",7,"emerald",1,"map",12),
        t("cartographer",2,"glass panes for emerald",11,"glass_pane",1,"emerald",12),
        t("cartographer",2,"ocean explorer map",13,"emerald",1,"filled_map",12,5,add=(1,"compass"),detail="Destination/content depends on the generated offer and version."),
        t("cartographer",3,"woodland explorer map",14,"emerald",1,"filled_map",12,10,add=(1,"compass"),detail="Destination/content depends on the generated offer and version."),
        t("cartographer",3,"compass for emerald",1,"compass",1,"emerald",12),
        t("cartographer",4,"item frame",7,"emerald",1,"item_frame",12), t("cartographer",4,"banner",3,"emerald",1,"white_banner",12,detail="Banner color varies by offer/version."),
        t("cartographer",5,"globe banner pattern",8,"emerald",1,"globe_banner_pattern",12),

        # Cleric
        t("cleric",1,"rotten flesh for emerald",32,"rotten_flesh",1,"emerald",16), t("cleric",1,"redstone dust",1,"emerald",2,"redstone",12),
        t("cleric",2,"gold for emerald",3,"gold_ingot",1,"emerald",12), t("cleric",2,"lapis lazuli",1,"emerald",1,"lapis_lazuli",12),
        t("cleric",3,"rabbit foot for emerald",2,"rabbit_foot",1,"emerald",12), t("cleric",3,"glowstone",4,"emerald",1,"glowstone",12),
        t("cleric",4,"scute for emerald",4,"scute",1,"emerald",12), t("cleric",4,"ender pearl",5,"emerald",1,"ender_pearl",12),
        t("cleric",5,"glass bottle for emerald",9,"glass_bottle",1,"emerald",12), t("cleric",5,"experience bottle",3,"emerald",1,"experience_bottle",12),

        # Farmer
        t("farmer",1,"wheat for emerald",20,"wheat",1,"emerald",16), t("farmer",1,"potatoes for emerald",26,"potato",1,"emerald",16),
        t("farmer",1,"carrots for emerald",22,"carrot",1,"emerald",16), t("farmer",1,"beetroot for emerald",15,"beetroot",1,"emerald",16), t("farmer",1,"bread",1,"emerald",6,"bread",16),
        t("farmer",2,"pumpkin for emerald",6,"pumpkin",1,"emerald",12), t("farmer",2,"pumpkin pie",1,"emerald",4,"pumpkin_pie",12), t("farmer",2,"apple",1,"emerald",4,"apple",16),
        t("farmer",3,"melon for emerald",4,"melon",1,"emerald",12), t("farmer",3,"cookie",3,"emerald",18,"cookie",12),
        t("farmer",4,"cake",1,"emerald",1,"cake",12), t("farmer",4,"suspicious stew",1,"emerald",1,"suspicious_stew",12,detail="Stew effect varies by offer."),
        t("farmer",5,"golden carrot",3,"emerald",3,"golden_carrot",12), t("farmer",5,"glistering melon slice",4,"emerald",3,"glistering_melon_slice",12),

        # Fisherman
        t("fisherman",1,"string for emerald",20,"string",1,"emerald",16), t("fisherman",1,"coal for emerald",15,"coal",1,"emerald",16),
        t("fisherman",1,"cooked cod service",1,"emerald",6,"cooked_cod",16,add=(6,"cod")),
        t("fisherman",2,"cod for emerald",15,"cod",1,"emerald",16), t("fisherman",2,"campfire",2,"emerald",1,"campfire",12),
        t("fisherman",3,"salmon for emerald",13,"salmon",1,"emerald",16), t("fisherman",3,"enchanted fishing rod",7,"emerald",1,"fishing_rod",3,10,detail="Enchantments and final price vary."),
        t("fisherman",4,"tropical fish for emerald",6,"tropical_fish",1,"emerald",12), t("fisherman",5,"pufferfish for emerald",4,"pufferfish",1,"emerald",12), t("fisherman",5,"boat",1,"emerald",1,"oak_boat",12,detail="Boat wood type varies with villager biome/version."),

        # Fletcher
        t("fletcher",1,"sticks for emerald",32,"stick",1,"emerald",16), t("fletcher",1,"arrows",1,"emerald",16,"arrow",12),
        t("fletcher",2,"flint for emerald",26,"flint",1,"emerald",12), t("fletcher",2,"bow",2,"emerald",1,"bow",12),
        t("fletcher",3,"string for emerald",14,"string",1,"emerald",16), t("fletcher",3,"crossbow",3,"emerald",1,"crossbow",12),
        t("fletcher",4,"feathers for emerald",24,"feather",1,"emerald",16), t("fletcher",4,"enchanted bow",2,"emerald",1,"bow",3,15,detail="Enchantments and price vary."),
        t("fletcher",5,"tripwire hooks for emerald",8,"tripwire_hook",1,"emerald",12), t("fletcher",5,"enchanted crossbow",3,"emerald",1,"crossbow",3,30,detail="Enchantments and price vary."),
        t("fletcher",5,"tipped arrows",2,"emerald",5,"tipped_arrow",12,30,add=(5,"arrow"),detail="Potion effect varies by offer/version."),

        # Leatherworker
        t("leatherworker",1,"leather for emerald",6,"leather",1,"emerald",16), t("leatherworker",1,"leather pants",3,"emerald",1,"leather_leggings",12,detail="Color may vary."),
        t("leatherworker",1,"leather tunic",7,"emerald",1,"leather_chestplate",12,detail="Color may vary."), t("leatherworker",2,"flint for emerald",26,"flint",1,"emerald",12),
        t("leatherworker",2,"leather cap",5,"emerald",1,"leather_helmet",12,detail="Color may vary."), t("leatherworker",2,"leather boots",4,"emerald",1,"leather_boots",12,detail="Color may vary."),
        t("leatherworker",3,"rabbit hide for emerald",9,"rabbit_hide",1,"emerald",12), t("leatherworker",3,"leather tunic premium",7,"emerald",1,"leather_chestplate",12,detail="Color may vary."),
        t("leatherworker",4,"scute for emerald",4,"scute",1,"emerald",12), t("leatherworker",4,"leather horse armor",6,"emerald",1,"leather_horse_armor",12), t("leatherworker",5,"saddle",6,"emerald",1,"saddle",12),

        # Librarian — books can appear at several levels depending on offer table/version.
        t("librarian",1,"paper for emerald",24,"paper",1,"emerald",16), t("librarian",1,"bookshelf",9,"emerald",1,"bookshelf",12),
        t("librarian",1,"enchanted book",5,"emerald",1,"enchanted_book",12,1,add=(1,"book"),detail="Random enchantment and price; exact trade generation is version-dependent."),
        t("librarian",2,"books for emerald",4,"book",1,"emerald",12), t("librarian",2,"lantern",1,"emerald",1,"lantern",12),
        t("librarian",2,"enchanted book apprentice",5,"emerald",1,"enchanted_book",12,5,add=(1,"book"),detail="Random enchantment and price."),
        t("librarian",3,"ink sac for emerald",5,"ink_sac",1,"emerald",12), t("librarian",3,"glass",1,"emerald",4,"glass",12),
        t("librarian",3,"enchanted book journeyman",5,"emerald",1,"enchanted_book",12,10,add=(1,"book"),detail="Random enchantment and price."),
        t("librarian",4,"writable book for emerald",2,"writable_book",1,"emerald",12), t("librarian",4,"clock",5,"emerald",1,"clock",12), t("librarian",4,"compass",4,"emerald",1,"compass",12),
        t("librarian",4,"enchanted book expert",5,"emerald",1,"enchanted_book",12,15,add=(1,"book"),detail="Random enchantment and price."),
        t("librarian",5,"name tag",20,"emerald",1,"name_tag",12,30),

        # Mason / stone mason
        t("mason",1,"clay for emerald",10,"clay_ball",1,"emerald",16), t("mason",1,"brick",1,"emerald",10,"brick",16),
        t("mason",2,"stone for emerald",20,"stone",1,"emerald",16), t("mason",2,"chiseled stone bricks",1,"emerald",4,"chiseled_stone_bricks",16),
        t("mason",3,"granite for emerald",16,"granite",1,"emerald",16), t("mason",3,"andesite for emerald",16,"andesite",1,"emerald",16), t("mason",3,"diorite for emerald",16,"diorite",1,"emerald",16),
        t("mason",3,"polished granite",1,"emerald",4,"polished_granite",16), t("mason",3,"polished andesite",1,"emerald",4,"polished_andesite",16), t("mason",3,"polished diorite",1,"emerald",4,"polished_diorite",16),
        t("mason",4,"quartz for emerald",12,"quartz",1,"emerald",12), t("mason",4,"terracotta",1,"emerald",1,"terracotta",12,detail="Color varies by offer."), t("mason",4,"glazed terracotta",1,"emerald",1,"white_glazed_terracotta",12,detail="Color varies by offer."),
        t("mason",5,"quartz pillar",1,"emerald",1,"quartz_pillar",12), t("mason",5,"quartz block",1,"emerald",1,"quartz_block",12),

        # Shepherd
        t("shepherd",1,"white wool for emerald",18,"white_wool",1,"emerald",16), t("shepherd",1,"brown wool for emerald",18,"brown_wool",1,"emerald",16), t("shepherd",1,"black wool for emerald",18,"black_wool",1,"emerald",16), t("shepherd",1,"gray wool for emerald",18,"gray_wool",1,"emerald",16), t("shepherd",1,"shears",2,"emerald",1,"shears",12),
        t("shepherd",2,"dye for emerald",12,"white_dye",1,"emerald",16,detail="Dye color varies by offer."), t("shepherd",2,"colored wool",1,"emerald",1,"blue_wool",16,detail="Wool color varies by offer."),
        t("shepherd",3,"dye for emerald journeyman",12,"red_dye",1,"emerald",16,detail="Dye color varies by offer."), t("shepherd",3,"carpet",1,"emerald",4,"blue_carpet",16,detail="Carpet color varies by offer."),
        t("shepherd",4,"banner",3,"emerald",1,"white_banner",12,detail="Banner color varies by offer."), t("shepherd",5,"painting",2,"emerald",3,"painting",12),

        # Toolsmith
        t("toolsmith",1,"coal for emerald",15,"coal",1,"emerald",16), t("toolsmith",1,"stone axe",1,"emerald",1,"stone_axe",12), t("toolsmith",1,"stone shovel",1,"emerald",1,"stone_shovel",12), t("toolsmith",1,"stone pickaxe",1,"emerald",1,"stone_pickaxe",12), t("toolsmith",1,"stone hoe",1,"emerald",1,"stone_hoe",12),
        t("toolsmith",2,"iron for emerald",4,"iron_ingot",1,"emerald",12), t("toolsmith",2,"bell",36,"emerald",1,"bell",12),
        t("toolsmith",3,"flint for emerald",30,"flint",1,"emerald",12), t("toolsmith",3,"enchanted iron axe",6,"emerald",1,"iron_axe",3,10,detail="Enchantments and price vary."), t("toolsmith",3,"enchanted iron shovel",5,"emerald",1,"iron_shovel",3,10,detail="Enchantments and price vary."), t("toolsmith",3,"enchanted iron pickaxe",8,"emerald",1,"iron_pickaxe",3,10,detail="Enchantments and price vary."),
        t("toolsmith",4,"diamond for emerald",1,"diamond",1,"emerald",12), t("toolsmith",4,"enchanted diamond hoe",4,"emerald",1,"diamond_hoe",3,15,detail="Enchantments and price vary."),
        t("toolsmith",5,"enchanted diamond axe",17,"emerald",1,"diamond_axe",3,30,detail="Enchantments and price vary."), t("toolsmith",5,"enchanted diamond shovel",10,"emerald",1,"diamond_shovel",3,30,detail="Enchantments and price vary."), t("toolsmith",5,"enchanted diamond pickaxe",18,"emerald",1,"diamond_pickaxe",3,30,detail="Enchantments and price vary."),

        # Weaponsmith
        t("weaponsmith",1,"coal for emerald",15,"coal",1,"emerald",16), t("weaponsmith",1,"iron axe",3,"emerald",1,"iron_axe",12), t("weaponsmith",1,"enchanted iron sword",7,"emerald",1,"iron_sword",3,1,detail="Enchantments and price vary."),
        t("weaponsmith",2,"iron for emerald",4,"iron_ingot",1,"emerald",12), t("weaponsmith",2,"bell",36,"emerald",1,"bell",12),
        t("weaponsmith",3,"flint for emerald",24,"flint",1,"emerald",12), t("weaponsmith",4,"diamond for emerald",1,"diamond",1,"emerald",12), t("weaponsmith",4,"enchanted diamond axe",12,"emerald",1,"diamond_axe",3,15,detail="Enchantments and price vary."),
        t("weaponsmith",5,"enchanted diamond sword",17,"emerald",1,"diamond_sword",3,30,detail="Enchantments and price vary."),
    ]
    return sorted(rows, key=lambda trade: (trade.profession, trade.level, trade.name))


def complete_reference(existing: list[Trade]) -> list[Trade]:
    """Merge the comprehensive reference over the older sparse fallback."""
    rows = list(existing); seen = {(r.profession, r.level, r.name, r.wants_id, r.gives_id) for r in rows}
    for trade in reference_trades():
        key = (trade.profession, trade.level, trade.name, trade.wants_id, trade.gives_id)
        if key not in seen:
            rows.append(trade); seen.add(key)
    return sorted(rows, key=lambda trade: (trade.profession, trade.level, trade.name))
