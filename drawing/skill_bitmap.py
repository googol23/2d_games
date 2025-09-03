from PIL import Image, ImageDraw, ImageFont
from character import Character

def skills_bitmap(c:Character, width: int = 300, padding: int = 10, line_height: int = 25):
    """
    Returns a PIL Image (RGBA) representing the player's skills with transparency.
    Uses player.skill_set which contains Skill objects.
    """
    font = ImageFont.load_default()

    # Suppose you want to align colons after the longest skill name
    max_name_length = max(len(name) for name, skill in c.skills_set.items())

    # Prepare lines from the SkillSet
    lines = [f"{name:<{max_name_length}}: {skill.level:>4} ({skill.points:>4}/{skill.points_to_next_level})" for name, skill in c.skills_set.items()]

    # Compute dynamic width based on longest line
    width = int(max(font.getlength(line) for line in lines) + 2 * padding)

    # Compute height
    height = padding * 2 + line_height * (len(lines) + 1)

    # Create transparent image
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw title
    draw.text((padding, padding), f"=== {c.name} ===", font=font, fill=(255, 255, 255, 255))

    # Draw each skill
    y = padding + line_height
    for name, skill in c.skills_set.items():
        draw.text((padding, y), f"{name:<13}: {skill.level:>4} ({skill.points:>4}/{skill.points_to_next_level})", font=font, fill=(255, 255, 255, 255))
        y += line_height

    # Optionally save image
    img.save(f"{c.name}_skills.png")
    return img
