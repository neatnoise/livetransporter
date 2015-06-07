# livetransporter
Aktualnie jest działająca wczesna wersja aplikacji, posiada następujące feature'y:
- automatyczne wykrywanie streamu gdy jest online (wsparcie hitbox i twitch)
- pobieranie na żywo livestreamu w czasie trwania live (wsparcie hitbox i twitch)
- cięcie odcinków live na podstawie zmiany gry na serwisie streamującym (wsparcie hitbox i twitch)
- cięcie odcinków live na podstawie dobrowolnego limitu czasowego odcinków (wsparcie hitbox i twitch)
- automatyczny upload streamu na serwis youtube (jako niepubliczny) po zmianie gry, po przekroczeniu ustawionego limitu czasowego odcinka (wsparcie hitbox i twitch)
- zachowanie najlepszej oryginalnej jakości live (stream nie jest konwertowany ani kompresowany)
- program może działać 24h na dobę (nie musi) na zewnętrznym serwerze nie obciążając komputer i łącze streamera, jak również może działać na komputerze streamera

Cele aplikacji:
- zapewnienie kompletnej, spójnej historii live z serwisów streamerskich typu twitch, hitbox na youtube
- zachowanie najlepszej jakości video streamów na serwisie youtube
- działanie aplikacji w czasie trwania live, automatyczne cięcie materiału zależnie od potrzeb, ustawień i natychmiastowy upload na youtube po wykonaniu operacji cięcia
- oszczędzenie czasu streamera nad obrabianiem i wysyłaniem livestreamów na youtube
- bardzo małe obciążenie CPU w trakcie operacji pobierania, prostego cięcia i uploadu livestreamu

Planowane feature'y:
- manualne wywoływanie nagrywania live, cięcia live, uploadu live za pomocą bota chatowego lub innego interfejsu np. panel www 
- stworzenie prostego user friendly interfefejsu użytkownika (w tym momencie jest tylko konsolowe)
- automatyczne dodawanie intra, outra do nagranego streamu zależnie od streamowanej gry
