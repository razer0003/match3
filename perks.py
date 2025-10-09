"""
Perk System for Match 3 Game
Provides extensible perk framework with different perk types and effects
"""

import pygame
import json
import os
import random
import math
from enum import Enum
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


class PerkType(Enum):
    """Types of perks available"""
    PASSIVE = "passive"      # Always active effects
    TIMED = "timed"         # Effects with cooldowns/timers
    TRIGGER = "trigger"     # Effects that activate on specific events


class PerkRarity(Enum):
    """Perk rarity levels"""
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class BasePerk(ABC):
    """Base class for all perks"""
    
    def __init__(self, perk_id: str, name: str, description: str, 
                 perk_type: PerkType, rarity: PerkRarity = PerkRarity.COMMON):
        self.id = perk_id
        self.name = name
        self.description = description
        self.type = perk_type
        self.rarity = rarity
        self.sprite_path = None  # Path to perk icon sprite
        self.is_active = False
        
    @abstractmethod
    def activate(self, game_instance):
        """Called when perk is activated/equipped"""
        pass
        
    @abstractmethod
    def deactivate(self, game_instance):
        """Called when perk is deactivated/unequipped"""
        pass
        
    @abstractmethod
    def update(self, game_instance, dt: float):
        """Called every frame while perk is active"""
        pass
        
    def to_dict(self) -> Dict[str, Any]:
        """Serialize perk data"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type.value,
            'rarity': self.rarity.value,
            'is_active': self.is_active
        }


class PassivePerk(BasePerk):
    """Base class for passive perks (always active)"""
    
    def __init__(self, perk_id: str, name: str, description: str, rarity: PerkRarity = PerkRarity.COMMON):
        super().__init__(perk_id, name, description, PerkType.PASSIVE, rarity)
    
    def update(self, game_instance, dt: float):
        """Passive perks don't need frame updates by default"""
        pass


class TimedPerk(BasePerk):
    """Base class for perks with timers/cooldowns"""
    
    def __init__(self, perk_id: str, name: str, description: str, 
                 cooldown: float, rarity: PerkRarity = PerkRarity.COMMON):
        super().__init__(perk_id, name, description, PerkType.TIMED, rarity)
        self.cooldown = cooldown
        self.timer = 0.0
        self.ready = True
        
    def update(self, game_instance, dt: float):
        """Update timer and check if effect should trigger"""
        if not self.ready:
            self.timer -= dt
            if self.timer <= 0:
                self.ready = True
                self.on_ready(game_instance)
        elif self.should_trigger(game_instance):
            self.trigger_effect(game_instance)
            self.timer = self.cooldown
            self.ready = False
            
    @abstractmethod
    def should_trigger(self, game_instance) -> bool:
        """Check if the perk should trigger its effect"""
        pass
        
    @abstractmethod
    def trigger_effect(self, game_instance):
        """Execute the perk's effect"""
        pass
        
    def on_ready(self, game_instance):
        """Called when perk becomes ready again (override if needed)"""
        pass


# Specific Perk Implementations
class X6MultiplierPerk(PassivePerk):
    """Allows combo multiplier to reach x6.0 instead of x5.0"""
    
    def __init__(self):
        super().__init__(
            "x6_multiplier",
            "X6 Multiplier", 
            "Combo multiplier cap increased from x5.0 to x6.0",
            PerkRarity.RARE
        )
        
    def activate(self, game_instance):
        """Increase max combo multiplier"""
        game_instance.max_combo_multiplier = 6.0
        self.is_active = True
        
    def deactivate(self, game_instance):
        """Reset max combo multiplier"""
        game_instance.max_combo_multiplier = 5.0
        self.is_active = False


class NoYellowPerk(PassivePerk):
    """Removes yellow tiles from generation"""
    
    def __init__(self):
        super().__init__(
            "no_yellow",
            "No Yellow",
            "Yellow tiles are replaced with other colors during generation",
            PerkRarity.COMMON
        )
        
    def activate(self, game_instance):
        """Enable yellow tile replacement"""
        game_instance.no_yellow_tiles = True
        if hasattr(game_instance, 'update_yellow_tile_exclusion'):
            game_instance.update_yellow_tile_exclusion()
        self.is_active = True
        
    def deactivate(self, game_instance):
        """Disable yellow tile replacement"""
        game_instance.no_yellow_tiles = False
        if hasattr(game_instance, 'update_yellow_tile_exclusion'):
            game_instance.update_yellow_tile_exclusion()
        self.is_active = False


class FastMultiplierPerk(PassivePerk):
    """Reduces multiplier increase interval from 10s to 7.5s"""
    
    def __init__(self):
        super().__init__(
            "fast_multiplier",
            "Quick Boost",
            "Combo multiplier increases every 7.5 seconds instead of 10",
            PerkRarity.COMMON
        )
        
    def activate(self, game_instance):
        """Reduce multiplier interval"""
        game_instance.combo_multiplier_interval = 7.5
        self.is_active = True
        
    def deactivate(self, game_instance):
        """Reset multiplier interval"""
        game_instance.combo_multiplier_interval = 10.0
        self.is_active = False


class FireballPerk(TimedPerk):
    """Launches fireballs every 30 seconds that create 3x3 explosions"""
    
    def __init__(self):
        super().__init__(
            "fireball",
            "Fireball Rain",
            "Every 30 seconds, a fireball strikes a random tile with 3x3 explosion",
            30.0,  # 30 second cooldown
            PerkRarity.EPIC
        )
        self.fireball_sprite = None
        
    def activate(self, game_instance):
        """Load fireball sprite and initialize"""
        try:
            self.fireball_sprite = pygame.image.load("assets/sprites/fireball.png")
        except:
            # Create placeholder if sprite not found
            self.fireball_sprite = pygame.Surface((32, 32))
            self.fireball_sprite.fill((255, 100, 0))  # Orange placeholder
        self.is_active = True
        
    def deactivate(self, game_instance):
        """Clean up fireball resources"""
        self.fireball_sprite = None
        self.is_active = False
        
    def should_trigger(self, game_instance) -> bool:
        """Fireball triggers automatically when timer is ready"""
        return True
        
    def trigger_effect(self, game_instance):
        """Launch a fireball at random position"""
        if hasattr(game_instance, 'launch_fireball'):
            game_instance.launch_fireball()


class PerkManager:
    """Manages all perks, selection, and persistence"""
    
    def __init__(self):
        self.available_perks: Dict[str, BasePerk] = {}
        self.selected_perks: List[BasePerk] = []
        self.max_selected = 3
        self.save_file = "perk_data.json"
        
        # Initialize all available perks
        self._initialize_perks()
        
    def _initialize_perks(self):
        """Create all available perks"""
        perks = [
            X6MultiplierPerk(),
            NoYellowPerk(),
            FastMultiplierPerk(),
            FireballPerk()
        ]
        
        for perk in perks:
            self.available_perks[perk.id] = perk
            
    def get_available_perks(self) -> List[BasePerk]:
        """Get list of all available perks"""
        return list(self.available_perks.values())
        
    def select_perk(self, perk_id: str, slot: int, game_instance) -> bool:
        """Select a perk for a specific slot (0-2)"""
        if slot < 0 or slot >= self.max_selected:
            return False
            
        if perk_id not in self.available_perks:
            return False
            
        # Deactivate current perk in slot if any
        if slot < len(self.selected_perks) and self.selected_perks[slot]:
            self.selected_perks[slot].deactivate(game_instance)
            
        # Ensure selected_perks list is the right size
        while len(self.selected_perks) <= slot:
            self.selected_perks.append(None)
            
        # Activate new perk
        perk = self.available_perks[perk_id]
        self.selected_perks[slot] = perk
        perk.activate(game_instance)
        
        return True
        
    def remove_perk(self, slot: int, game_instance) -> bool:
        """Remove perk from slot"""
        if slot < 0 or slot >= len(self.selected_perks):
            return False
            
        if self.selected_perks[slot]:
            self.selected_perks[slot].deactivate(game_instance)
            self.selected_perks[slot] = None
            
        return True
        
    def update_perks(self, game_instance, dt: float):
        """Update all active perks"""
        for perk in self.selected_perks:
            if perk and perk.is_active:
                perk.update(game_instance, dt)
                
    def save_selection(self):
        """Save current perk selection to file"""
        data = {
            'selected_perks': [perk.id if perk else None for perk in self.selected_perks]
        }
        
        try:
            with open(self.save_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save perks: {e}")
            return False
            
    def load_selection(self, game_instance):
        """Load perk selection from file"""
        try:
            if not os.path.exists(self.save_file):
                return False
                
            with open(self.save_file, 'r') as f:
                data = json.load(f)
                
            selected_ids = data.get('selected_perks', [])
            
            # Clear current selection
            for i, perk in enumerate(self.selected_perks):
                if perk:
                    perk.deactivate(game_instance)
                    
            self.selected_perks = []
            
            # Restore selection
            for i, perk_id in enumerate(selected_ids):
                if perk_id and i < self.max_selected:
                    self.select_perk(perk_id, i, game_instance)
                    
            return True
        except Exception as e:
            print(f"Failed to load perks: {e}")
            return False


# GUI Classes for Perk Selection
class PerkSelectionGUI:
    """Temporary GUI for selecting perks"""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.visible = False
        
        # GUI layout
        self.gui_width = 600
        self.gui_height = 400
        self.gui_x = (screen_width - self.gui_width) // 2
        self.gui_y = (screen_height - self.gui_height) // 2
        
        # Perk slots (3 slots at top)
        self.slot_size = 80
        self.slot_spacing = 20
        self.slots_start_x = self.gui_x + 50
        self.slots_y = self.gui_y + 50
        
        # Perk browser (bottom area)
        self.browser_y = self.gui_y + 150
        self.browser_height = 180
        self.perk_icon_size = 60
        self.perk_spacing = 10
        
        # Buttons
        self.save_button_rect = pygame.Rect(self.gui_x + self.gui_width - 120, 
                                          self.gui_y + self.gui_height - 50, 100, 30)
        
        # State
        self.selected_slot = None  # Which slot is being edited
        self.perk_browser_visible = False
        
        # Colors
        self.bg_color = (50, 50, 50, 200)
        self.slot_color = (80, 80, 80)
        self.slot_selected_color = (120, 120, 120)
        self.button_color = (100, 100, 150)
        self.text_color = (255, 255, 255)
        
    def toggle_visibility(self):
        """Toggle GUI visibility"""
        self.visible = not self.visible
        if not self.visible:
            self.perk_browser_visible = False
            self.selected_slot = None
            
    def handle_click(self, pos: tuple, perk_manager: PerkManager, game_instance) -> bool:
        """Handle mouse clicks, return True if click was handled"""
        if not self.visible:
            return False
            
        # Check slot clicks
        for i in range(3):
            slot_x = self.slots_start_x + i * (self.slot_size + self.slot_spacing)
            slot_rect = pygame.Rect(slot_x, self.slots_y, self.slot_size, self.slot_size)
            
            if slot_rect.collidepoint(pos):
                self.selected_slot = i
                self.perk_browser_visible = True
                return True
                
        # Check perk browser clicks
        if self.perk_browser_visible and self.selected_slot is not None:
            available_perks = perk_manager.get_available_perks()
            for i, perk in enumerate(available_perks):
                perk_x = self.gui_x + 20 + i * (self.perk_icon_size + self.perk_spacing)
                perk_y = self.browser_y + 20
                perk_rect = pygame.Rect(perk_x, perk_y, self.perk_icon_size, self.perk_icon_size)
                
                if perk_rect.collidepoint(pos):
                    # Select this perk for the selected slot
                    perk_manager.select_perk(perk.id, self.selected_slot, game_instance)
                    self.perk_browser_visible = False
                    self.selected_slot = None
                    return True
                    
        # Check save button
        if self.save_button_rect.collidepoint(pos):
            perk_manager.save_selection()
            print("Perks saved!")
            return True
            
        return True  # Always consume clicks when GUI is visible
        
    def draw(self, screen: pygame.Surface, font: pygame.font.Font, perk_manager: PerkManager):
        """Draw the perk selection GUI"""
        if not self.visible:
            return
            
        # Create semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Draw main GUI background
        gui_surface = pygame.Surface((self.gui_width, self.gui_height))
        gui_surface.fill((60, 60, 60))
        screen.blit(gui_surface, (self.gui_x, self.gui_y))
        
        # Draw title
        title_text = font.render("Select Perks (P to close)", True, self.text_color)
        screen.blit(title_text, (self.gui_x + 20, self.gui_y + 10))
        
        # Draw perk slots
        for i in range(3):
            slot_x = self.slots_start_x + i * (self.slot_size + self.slot_spacing)
            slot_color = self.slot_selected_color if i == self.selected_slot else self.slot_color
            
            pygame.draw.rect(screen, slot_color, 
                           (slot_x, self.slots_y, self.slot_size, self.slot_size))
            pygame.draw.rect(screen, self.text_color, 
                           (slot_x, self.slots_y, self.slot_size, self.slot_size), 2)
                           
            # Draw equipped perk if any
            if i < len(perk_manager.selected_perks) and perk_manager.selected_perks[i]:
                perk = perk_manager.selected_perks[i]
                perk_text = font.render(perk.name[:8], True, self.text_color)
                text_rect = perk_text.get_rect(center=(slot_x + self.slot_size//2, 
                                                     self.slots_y + self.slot_size//2))
                screen.blit(perk_text, text_rect)
                
        # Draw perk browser if visible
        if self.perk_browser_visible:
            # Browser background
            browser_rect = pygame.Rect(self.gui_x + 10, self.browser_y, 
                                     self.gui_width - 20, self.browser_height)
            pygame.draw.rect(screen, (40, 40, 40), browser_rect)
            pygame.draw.rect(screen, self.text_color, browser_rect, 2)
            
            # Browser title
            browser_title = font.render("Available Perks:", True, self.text_color)
            screen.blit(browser_title, (self.gui_x + 20, self.browser_y + 5))
            
            # Draw available perks
            available_perks = perk_manager.get_available_perks()
            for i, perk in enumerate(available_perks):
                perk_x = self.gui_x + 20 + i * (self.perk_icon_size + self.perk_spacing)
                perk_y = self.browser_y + 30
                
                # Perk icon background
                pygame.draw.rect(screen, (80, 80, 80), 
                               (perk_x, perk_y, self.perk_icon_size, self.perk_icon_size))
                pygame.draw.rect(screen, self.text_color, 
                               (perk_x, perk_y, self.perk_icon_size, self.perk_icon_size), 1)
                
                # Perk name (temporary text)
                perk_text = font.render(perk.name[:6], True, self.text_color)
                text_rect = perk_text.get_rect(center=(perk_x + self.perk_icon_size//2, 
                                                     perk_y + self.perk_icon_size//2))
                screen.blit(perk_text, text_rect)
                
                # Perk description below
                desc_text = font.render(perk.description[:40] + "...", True, (200, 200, 200))
                screen.blit(desc_text, (perk_x, perk_y + self.perk_icon_size + 5))
                
        # Draw save button
        pygame.draw.rect(screen, self.button_color, self.save_button_rect)
        pygame.draw.rect(screen, self.text_color, self.save_button_rect, 2)
        save_text = font.render("Save", True, self.text_color)
        save_rect = save_text.get_rect(center=self.save_button_rect.center)
        screen.blit(save_text, save_rect)