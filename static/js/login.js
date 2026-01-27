// Kod animacji sieci
document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('network-animation');
    const ctx = canvas.getContext('2d');
    
    // Ustaw wymiary canvas na pełny ekran
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    // Parametry animacji
    const particleCount = 200;
    const connectionDistance = 180;
    const particles = [];
    
    // Stwórz cząsteczki (węzły)
    for (let i = 0; i < particleCount; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            radius: Math.random() * 3 + 1,
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5,
            color: `rgba(${Math.floor(Math.random() * 50)}, ${Math.floor(Math.random() * 50)}, ${Math.floor(Math.random() * 50)}, ${Math.random() * 0.5 + 0.1})`,
            pulse: 0,
            pulseDirection: Math.random() > 0.5 ? 1 : -1
        });
    }
    
    // Funkcja rysująca animację
    function draw() {
        // Wyczyść canvas i dodaj tło
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Możesz tu ustawić kolor tła, aby eksperymentować z różnymi kolorami
        ctx.fillStyle = "#f0f8ff"; // Przykładowy kolor: jasnoniebieski
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Aktualizuj pozycje cząsteczek
        particles.forEach(p => {
            p.x += p.vx;
            p.y += p.vy;
        
        // Pulsowanie
        p.pulse += 0.01 * p.pulseDirection;
        if (p.pulse > 1 || p.pulse < 0) p.pulseDirection *= -1;
            
            // Odbijaj od krawędzi
            if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
            if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
            
            // Rysuj cząsteczkę z efektem pulsowania
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius * (1 + p.pulse * 0.3), 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.fill();
        });
        
        // Rysuj połączenia
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < connectionDistance) {
                    // Zmniejsz przezroczystość wraz z odległością
                    const opacity = 1 - (distance / connectionDistance);
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `rgba(100, 100, 100, ${opacity * 0.2})`;
                    ctx.lineWidth = 1;
                    ctx.stroke();
                }
            }
        }
        
        requestAnimationFrame(draw);
    }
    
    // Uruchom animację
    draw();
});