SET GLOBAL event_scheduler = ON;

delimiter |

create EVENT auto_decrease
ON SCHEDULE EVERY 2 SECOND 
DO 
begin
	update elec5622.petmon_pet set satiation = satiation - 1 where satiation > 0;
    update elec5622.petmon_pet set lush = lush - 1 where lush > 0;
    end |
    
delimiter ;
    
